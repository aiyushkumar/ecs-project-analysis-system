import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query, status
from fastapi.responses import FileResponse

from backend.app.core.config import settings
from backend.app.core.database import DatabaseManager
from backend.app.core.security import (
    generate_secure_token, hash_token, sanitize_filename,
    validate_pdf_signature, validate_zip_signature, safe_extract_zip
)
from backend.app.models.schemas import (
    AnalysisJobCreateResponse, BatchJobCreateResponse,
    AnalysisJobStatusResponse, BatchStatusResponse,
    AnalysisResultResponse, JobStatus, ProcessingStage,
    SimilaritySummary, SourceEvidence, SimilarityMatchEvidence
)
from backend.app.api.dependencies import verify_job_access, verify_batch_access
from backend.app.workers.queue_manager import QueueManager
from backend.app.workers.tasks import generate_batch_zip

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analyze", tags=["Analysis"])

@router.post("/upload", response_model=list[AnalysisJobCreateResponse])
async def upload_reports(files: list[UploadFile] = File(...)):
    """
    Upload one or multiple PDF project reports.
    Validates files, generates cryptographically secure tokens, and dispatches to queue.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    responses = []

    for file in files:
        clean_name = sanitize_filename(file.filename or "report.pdf")
        if not clean_name.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDF.")

        # Read initial chunk to check magic bytes
        header = await file.read(1024)
        if b"%PDF-" not in header:
            raise HTTPException(status_code=400, detail=f"File {file.filename} does not contain valid PDF signature.")
        await file.seek(0)

        # Check file size limit
        content = await file.read()
        file_size = len(content)
        if file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(status_code=413, detail=f"File {file.filename} exceeds {settings.MAX_FILE_SIZE_MB}MB limit.")

        job_id = f"job_{uuid.uuid4().hex}"
        private_token = generate_secure_token()
        token_hash = hash_token(private_token)

        # Save to disk
        save_path = settings.UPLOAD_DIR / f"{job_id}_{clean_name}"
        with open(save_path, "wb") as f:
            f.write(content)

        # Create record in DB
        job_record = DatabaseManager.create_job(
            job_id=job_id,
            original_filename=clean_name,
            token_hash=token_hash,
            file_size=file_size
        )

        # Enqueue processing
        QueueManager.enqueue_job(job_id, save_path)

        responses.append(AnalysisJobCreateResponse(
            job_id=job_id,
            original_filename=clean_name,
            status=JobStatus.PENDING,
            stage=ProcessingStage.QUEUED,
            private_token=private_token,
            status_url=f"/api/analyze/status/{job_id}",
            result_url=f"/api/analyze/result/{job_id}?token={private_token}",
            created_at=datetime.utcnow()
        ))

    return responses

@router.post("/batch", response_model=BatchJobCreateResponse)
async def upload_batch(file: UploadFile = File(...)):
    """
    Upload a batch ZIP archive or bulk files (supporting > 300 reports).
    Extracts PDFs safely and schedules independent worker jobs with failure isolation.
    """
    clean_name = sanitize_filename(file.filename or "batch.zip")
    
    # Handle ZIP uploads
    if clean_name.lower().endswith(".zip"):
        content = await file.read()
        zip_temp_path = settings.TEMP_DIR / f"batch_{uuid.uuid4().hex}.zip"
        with open(zip_temp_path, "wb") as f:
            f.write(content)

        if not validate_zip_signature(zip_temp_path):
            zip_temp_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail="Invalid ZIP archive signature.")

        extract_dir = settings.TEMP_DIR / f"extract_{uuid.uuid4().hex}"
        try:
            pdf_files = safe_extract_zip(zip_temp_path, extract_dir)
        except Exception as e:
            zip_temp_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail=f"Archive extraction failed: {str(e)}")

        if not pdf_files:
            zip_temp_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail="No readable PDF files found inside ZIP archive.")

        if len(pdf_files) > settings.MAX_BATCH_SIZE:
            raise HTTPException(status_code=400, detail=f"Batch size {len(pdf_files)} exceeds maximum limit of {settings.MAX_BATCH_SIZE}.")

        batch_id = f"batch_{uuid.uuid4().hex}"
        batch_token = generate_secure_token()
        batch_token_hash = hash_token(batch_token)

        DatabaseManager.create_batch(batch_id, len(pdf_files), batch_token_hash)

        job_responses = []
        for pdf_path in pdf_files:
            job_id = f"job_{uuid.uuid4().hex}"
            dest_path = settings.UPLOAD_DIR / f"{job_id}_{pdf_path.name}"
            pdf_path.replace(dest_path)

            file_size = dest_path.stat().st_size
            DatabaseManager.create_job(
                job_id=job_id,
                original_filename=pdf_path.name,
                token_hash=batch_token_hash,  # Shared batch token can access all jobs
                batch_id=batch_id,
                file_size=file_size
            )

            QueueManager.enqueue_job(job_id, dest_path)

            job_responses.append(AnalysisJobCreateResponse(
                job_id=job_id,
                original_filename=pdf_path.name,
                status=JobStatus.PENDING,
                stage=ProcessingStage.QUEUED,
                private_token=batch_token,
                status_url=f"/api/analyze/status/{job_id}",
                result_url=f"/api/analyze/result/{job_id}?token={batch_token}",
                created_at=datetime.utcnow()
            ))

        # Cleanup temp zip
        zip_temp_path.unlink(missing_ok=True)

        return BatchJobCreateResponse(
            batch_id=batch_id,
            total_files=len(pdf_files),
            jobs=job_responses,
            private_token=batch_token,
            status_url=f"/api/analyze/batch/{batch_id}",
            download_url=f"/api/analyze/batch/{batch_id}/download?token={batch_token}",
            created_at=datetime.utcnow()
        )
    else:
        raise HTTPException(status_code=400, detail="Expected a .zip file for batch endpoint.")

@router.get("/status/{job_id}", response_model=AnalysisJobStatusResponse)
async def get_job_status(job_id: str):
    """Public real-time status tracker for a given analysis job."""
    job = DatabaseManager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found.")

    is_completed = job["status"] == "completed"
    
    return AnalysisJobStatusResponse(
        job_id=job["id"],
        batch_id=job.get("batch_id"),
        original_filename=job["original_filename"],
        file_size_bytes=job.get("file_size_bytes", 0),
        page_count=job.get("page_count", 0),
        word_count=job.get("word_count", 0),
        character_count=job.get("character_count", 0),
        status=JobStatus(job["status"]),
        stage=ProcessingStage(job["stage"]),
        stage_progress=job.get("stage_progress", 0),
        overall_similarity=job.get("overall_similarity", 0.0),
        error_message=job.get("error_message"),
        processing_duration_sec=job.get("processing_duration_sec"),
        download_available=is_completed and bool(job.get("report_path")),
        download_url=f"/api/analyze/download/{job_id}" if is_completed else None,
        created_at=datetime.fromisoformat(job["created_at"]) if isinstance(job["created_at"], str) else job["created_at"],
        updated_at=datetime.fromisoformat(job["updated_at"]) if isinstance(job["updated_at"], str) else job["updated_at"]
    )

@router.get("/result/{job_id}", response_model=AnalysisResultResponse)
async def get_job_result(job_id: str, job: dict = Depends(verify_job_access)):
    """
    Secure result retrieval requiring private cryptographic token.
    Returns complete similarity analysis, evidence, sources, and download link.
    """
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Analysis is still in progress or has failed.")

    sources_raw = DatabaseManager.get_job_sources(job_id)
    matches_raw = DatabaseManager.get_job_matches(job_id)

    top_sources = [
        SourceEvidence(
            source_id=s["id"],
            source_number=s["source_number"],
            title=s["title"],
            url=s["url"],
            category=s["category"],
            author_or_owner=s.get("author_or_owner") or "Unknown",
            publication_or_repo=s.get("publication_or_repo") or "",
            percentage=s.get("percentage", 0.0),
            match_count=s.get("match_count", 0),
            retrieved_at=datetime.fromisoformat(s["retrieved_at"]) if isinstance(s["retrieved_at"], str) else s["retrieved_at"]
        ) for s in sources_raw
    ]

    matches = [
        SimilarityMatchEvidence(
            match_id=m["id"],
            source_number=m["source_number"],
            source_title=m["source_title"],
            source_url=m["source_url"],
            source_category=m["source_category"],
            page_number=m["page_number"],
            section_name=m["section_name"],
            matched_text=m["matched_text"],
            source_excerpt=m["source_excerpt"],
            match_type=m["match_type"],
            confidence=m["confidence"],
            start_char=m.get("start_char", 0),
            end_char=m.get("end_char", 0)
        ) for m in matches_raw
    ]

    sections_list = json.loads(job.get("sections_json") or "[]")
    
    summary = SimilaritySummary(
        overall_similarity=job.get("overall_similarity", 0.0),
        internet_percentage=job.get("internet_percentage", 0.0),
        publications_percentage=job.get("publications_percentage", 0.0),
        crossref_percentage=job.get("crossref_percentage", 0.0),
        github_percentage=job.get("github_percentage", 0.0),
        exact_similarity=job.get("exact_similarity", 0.0),
        lexical_similarity=job.get("lexical_similarity", 0.0),
        semantic_similarity=job.get("semantic_similarity", 0.0),
        code_similarity=job.get("code_similarity", 0.0),
        calculation_method="Multi-Signal Hybrid Analysis (Exact, Lexical, Semantic, Code Token Union)",
        disclaimer="Similarity results are indicators for human interpretation and do not constitute an automatic verdict of academic misconduct."
    )

    created_dt = datetime.fromisoformat(job["created_at"]) if isinstance(job["created_at"], str) else job["created_at"]
    updated_dt = datetime.fromisoformat(job["updated_at"]) if isinstance(job["updated_at"], str) else job["updated_at"]

    return AnalysisResultResponse(
        job_id=job["id"],
        original_filename=job["original_filename"],
        report_id=f"ecs:{job['id'][:8]}",
        word_count=job.get("word_count", 0),
        character_count=job.get("character_count", 0),
        page_count=job.get("page_count", 0),
        file_size_mb=round((job.get("file_size_bytes", 0) / (1024 * 1024)), 2),
        submission_date=created_dt.strftime("%b %d, %Y %I:%M %p GMT+5:30"),
        report_date=updated_dt.strftime("%b %d, %Y %I:%M %p GMT+5:30"),
        processing_duration_seconds=job.get("processing_duration_sec", 0.0),
        similarity_summary=summary,
        top_sources=top_sources,
        matches=matches,
        sections_detected=sections_list,
        download_url=f"/api/analyze/download/{job_id}"
    )

@router.get("/download/{job_id}")
async def download_report(job_id: str, job: dict = Depends(verify_job_access)):
    """Downloads the generated RPi_CSR-style PDF report."""
    report_path_str = job.get("report_path")
    if not report_path_str:
        raise HTTPException(status_code=404, detail="PDF report not yet available.")
    
    report_path = Path(report_path_str)
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found on disk.")

    download_filename = f"ECS_Similarity_Report_{job['original_filename']}"
    return FileResponse(
        path=str(report_path),
        media_type="application/pdf",
        filename=download_filename
    )

@router.get("/batch/{batch_id}", response_model=BatchStatusResponse)
async def get_batch_status(batch_id: str):
    """Tracks overall progress for a batch of reports (supporting 300+ items)."""
    batch = DatabaseManager.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found.")

    jobs_raw = DatabaseManager.get_batch_jobs(batch_id)
    total = batch["total_files"]
    completed = batch["completed_files"]
    failed = batch["failed_files"]
    processing = total - (completed + failed)
    progress_pct = round(((completed + failed) / total * 100), 1) if total > 0 else 0.0

    job_statuses = [
        AnalysisJobStatusResponse(
            job_id=j["id"],
            batch_id=batch_id,
            original_filename=j["original_filename"],
            file_size_bytes=j.get("file_size_bytes", 0),
            page_count=j.get("page_count", 0),
            word_count=j.get("word_count", 0),
            character_count=j.get("character_count", 0),
            status=JobStatus(j["status"]),
            stage=ProcessingStage(j["stage"]),
            stage_progress=j.get("stage_progress", 0),
            overall_similarity=j.get("overall_similarity", 0.0),
            error_message=j.get("error_message"),
            processing_duration_sec=j.get("processing_duration_sec"),
            download_available=j["status"] == "completed" and bool(j.get("report_path")),
            download_url=f"/api/analyze/download/{j['id']}" if j["status"] == "completed" else None,
            created_at=datetime.fromisoformat(j["created_at"]) if isinstance(j["created_at"], str) else j["created_at"],
            updated_at=datetime.fromisoformat(j["updated_at"]) if isinstance(j["updated_at"], str) else j["updated_at"]
        ) for j in jobs_raw
    ]

    all_done = (completed + failed >= total)

    return BatchStatusResponse(
        batch_id=batch["id"],
        total_files=total,
        completed_files=completed,
        failed_files=failed,
        processing_files=max(0, processing),
        status=JobStatus(batch["status"]),
        progress_percentage=progress_pct,
        jobs=job_statuses,
        zip_download_available=all_done and completed > 0,
        zip_download_url=f"/api/analyze/batch/{batch_id}/download" if all_done and completed > 0 else None,
        created_at=datetime.fromisoformat(batch["created_at"]) if isinstance(batch["created_at"], str) else batch["created_at"],
        updated_at=datetime.fromisoformat(batch["updated_at"]) if isinstance(batch["updated_at"], str) else batch["updated_at"]
    )

@router.get("/batch/{batch_id}/download")
async def download_batch_zip(batch_id: str, batch: dict = Depends(verify_batch_access)):
    """Downloads all completed reports in a single ZIP bundle."""
    zip_path = generate_batch_zip(batch_id)
    if not zip_path or not zip_path.exists():
        raise HTTPException(status_code=404, detail="Batch reports ZIP could not be generated.")

    return FileResponse(
        path=str(zip_path),
        media_type="application/zip",
        filename=f"ECS_Batch_Reports_{batch_id[:8]}.zip"
    )

@router.post("/batch/{batch_id}/retry-failed")
async def retry_failed_in_batch(batch_id: str, batch: dict = Depends(verify_batch_access)):
    """Retries any failed reports in a batch without affecting completed ones."""
    retried_count = QueueManager.retry_failed_jobs(batch_id)
    return {"message": f"Retrying {retried_count} failed jobs in batch {batch_id}."}
