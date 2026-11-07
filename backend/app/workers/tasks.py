import asyncio
import logging
import time
import zipfile
from datetime import datetime
from pathlib import Path

from backend.app.core.config import settings
from backend.app.core.database import DatabaseManager
from backend.app.core.security import compute_file_sha256, validate_pdf_signature
from backend.app.models.schemas import ProcessingStage, JobStatus
from backend.app.pdf_processing.extractor import extract_pdf_document
from backend.app.pdf_processing.segmenter import segment_report
from backend.app.connectors.github_connector import GitHubConnector
from backend.app.connectors.scholarly_connector import ScholarlyConnector
from backend.app.connectors.web_connector import WebSearchConnector
from backend.app.ai_engine.hybrid_engine import HybridSimilarityEngine
from backend.app.report_generator.rpi_csr_generator import RPiCSRReportGenerator

logger = logging.getLogger(__name__)

async def run_analysis_pipeline(job_id: str, file_path_str: str) -> bool:
    """
    Executes the complete 8-stage AI similarity pipeline for a single PDF.
    Isolates failures so other jobs in a batch continue unimpeded.
    """
    start_time = time.time()
    file_path = Path(file_path_str)

    try:
        # Stage 1: Upload Validation
        DatabaseManager.update_job_stage(job_id, ProcessingStage.UPLOAD_VALIDATION.value, stage_progress=10)
        if not file_path.exists():
            raise FileNotFoundError(f"Uploaded file not found on disk: {file_path.name}")
        
        if not validate_pdf_signature(file_path):
            raise ValueError("File signature validation failed: Not a valid PDF document.")
        
        file_hash = compute_file_sha256(file_path)

        # Stage 2: PDF Text Extraction
        DatabaseManager.update_job_stage(job_id, ProcessingStage.PDF_TEXT_EXTRACTION.value, stage_progress=25)
        extracted_doc = extract_pdf_document(file_path)

        # Stage 3: Document Understanding
        DatabaseManager.update_job_stage(job_id, ProcessingStage.DOCUMENT_UNDERSTANDING.value, stage_progress=40)
        segmented = segment_report(extracted_doc)

        # Extract distinctive queries from Title, Abstract, and Key Sections
        import re
        clean_title = re.sub(r'[\d_\-]+', ' ', Path(extracted_doc.filename).stem).strip()
        queries = [clean_title] if len(clean_title) >= 4 else ["Project Report"]
        
        # Add abstract excerpt if found
        if "Abstract" in segmented.sections:
            abs_text = " ".join([p.text for p in segmented.sections["Abstract"][:2]])
            if abs_text:
                queries.append(abs_text[:120])
                
        # Add keywords from text
        words = [w for w in extracted_doc.full_text.split() if len(w) > 5 and w.isalpha()]
        if len(words) >= 4:
            queries.append(" ".join(words[:4]))

        # Stage 4: GitHub Source Discovery
        DatabaseManager.update_job_stage(job_id, ProcessingStage.GITHUB_SOURCE_DISCOVERY.value, stage_progress=55)
        gh_connector = GitHubConnector()
        gh_sources = await gh_connector.search(queries, max_results=5)

        # Stage 5: Research Paper Analysis
        DatabaseManager.update_job_stage(job_id, ProcessingStage.RESEARCH_PAPER_ANALYSIS.value, stage_progress=70)
        scholar_connector = ScholarlyConnector()
        scholar_sources = await scholar_connector.search(queries, max_results=8)

        # Stage 6: Internet Source Analysis
        DatabaseManager.update_job_stage(job_id, ProcessingStage.INTERNET_SOURCE_ANALYSIS.value, stage_progress=80)
        web_connector = WebSearchConnector()
        web_sources = await web_connector.search(queries, max_results=6)

        # Combine all retrieved candidate sources
        all_candidate_sources = gh_sources + scholar_sources + web_sources

        # Stage 7: Similarity Detection
        DatabaseManager.update_job_stage(job_id, ProcessingStage.SIMILARITY_DETECTION.value, stage_progress=90)
        hybrid_engine = HybridSimilarityEngine()
        summary, top_sources, matches = hybrid_engine.analyze(segmented, all_candidate_sources)

        # Stage 8: PDF Report Generation (RPi_CSR format)
        DatabaseManager.update_job_stage(job_id, ProcessingStage.PDF_REPORT_GENERATION.value, stage_progress=95)
        report_filename = f"ECS_Report_{job_id[:8]}_{file_path.stem}.pdf"
        report_path = settings.REPORT_DIR / report_filename

        generator = RPiCSRReportGenerator(report_path)
        generator.generate(
            job_id=job_id,
            original_filename=extracted_doc.filename,
            word_count=extracted_doc.word_count,
            char_count=extracted_doc.char_count,
            page_count=extracted_doc.page_count,
            file_size_bytes=extracted_doc.file_size_bytes,
            submission_time=datetime.utcnow(),
            summary=summary,
            top_sources=top_sources,
            matches=matches,
            sections=segmented.sections,
            original_pdf_path=file_path
        )

        duration = time.time() - start_time
        
        # Complete job in database
        DatabaseManager.complete_job(
            job_id=job_id,
            page_count=extracted_doc.page_count,
            word_count=extracted_doc.word_count,
            char_count=extracted_doc.char_count,
            file_hash=file_hash,
            overall_similarity=summary.overall_similarity,
            internet_percentage=summary.internet_percentage,
            publications_percentage=summary.publications_percentage,
            crossref_percentage=summary.crossref_percentage,
            github_percentage=summary.github_percentage,
            exact_similarity=summary.exact_similarity,
            lexical_similarity=summary.lexical_similarity,
            semantic_similarity=summary.semantic_similarity,
            code_similarity=summary.code_similarity,
            sections=segmented.detected_section_names,
            report_path=str(report_path),
            duration_sec=duration,
            sources=[s.model_dump() for s in top_sources],
            matches=[m.model_dump() for m in matches]
        )

        logger.info(f"Successfully completed analysis job {job_id} in {duration:.2f}s")
        return True

    except Exception as e:
        logger.exception(f"Error processing analysis job {job_id}: {e}")
        DatabaseManager.fail_job(job_id, str(e))
        return False

def sync_run_pipeline(job_id: str, file_path_str: str):
    """Synchronous wrapper for thread pool or Celery execution."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_analysis_pipeline(job_id, file_path_str))
    finally:
        loop.close()

# Celery Task definition (used if Celery worker is active)
try:
    from backend.app.workers.celery_app import celery_app
    @celery_app.task(bind=True, max_retries=2)
    def celery_process_pdf_job(self, job_id: str, file_path_str: str):
        try:
            sync_run_pipeline(job_id, file_path_str)
        except Exception as exc:
            logger.error(f"Celery task failed for job {job_id}: {exc}")
            raise self.retry(exc=exc, countdown=5)
except Exception as e:
    celery_process_pdf_job = None

def generate_batch_zip(batch_id: str) -> Path | None:
    """Generates a ZIP archive containing all completed PDF reports for a batch."""
    jobs = DatabaseManager.get_batch_jobs(batch_id)
    if not jobs:
        return None

    zip_filename = f"ECS_Batch_Reports_{batch_id[:8]}.zip"
    zip_path = settings.REPORT_DIR / zip_filename

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for j in jobs:
            if j.get("status") == "completed" and j.get("report_path"):
                r_path = Path(j["report_path"])
                if r_path.exists():
                    zf.write(r_path, arcname=r_path.name)

    DatabaseManager.set_batch_zip(batch_id, str(zip_path))
    return zip_path
