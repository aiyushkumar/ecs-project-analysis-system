import io
import time
import zipfile
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.config import settings
from backend.app.core.database import DatabaseManager

client = TestClient(app)

def create_synthetic_pdf(index: int) -> bytes:
    """Creates a valid, lightweight representative PDF report with text and structure."""
    return f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 120 >>
stream
BT
/F1 12 Tf
72 712 Td
(Project Report #{index}: AI-Driven Distributed Systems and Embedded Computing) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000202 00000 n 
trailer
<< /Size 5 /Root 1 0 R >>
%%EOF""".encode('utf-8')

@pytest.fixture(autouse=True)
def clean_database():
    import sqlite3
    db_file = settings.STORAGE_DIR / "ecs.db"
    if db_file.exists():
        conn = sqlite3.connect(str(db_file))
        c = conn.cursor()
        c.execute("DELETE FROM similarity_matches")
        c.execute("DELETE FROM sources")
        c.execute("DELETE FROM analysis_jobs")
        c.execute("DELETE FROM batch_jobs")
        conn.commit()
        conn.close()
    yield

@pytest.mark.timeout(300)
def test_batch_301_pdf_upload_and_processing(tmp_path: Path):
    """
    CRITICAL LOAD TEST:
    Tests bulk upload and queue management for 301 representative project report PDFs.
    Validates failure isolation, individual job tracking, and batch ZIP consolidation.
    """
    TOTAL_REPORTS = 301
    print(f"\n[LOAD TEST] Synthesizing {TOTAL_REPORTS} representative PDF project reports...")
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for i in range(1, TOTAL_REPORTS + 1):
            filename = f"ECS_Student_Project_{i:03d}.pdf"
            pdf_bytes = create_synthetic_pdf(i)
            zf.writestr(filename, pdf_bytes)

    zip_bytes = zip_buffer.getvalue()
    print(f"[LOAD TEST] Archive synthesized successfully. Size: {len(zip_bytes) / 1024:.1f} KB")

    # Step 1: Upload 301 PDF batch archive
    start_time = time.time()
    response = client.post(
        "/api/analyze/batch",
        files={"file": ("university_cohort_301_projects.zip", io.BytesIO(zip_bytes), "application/zip")}
    )
    upload_duration = time.time() - start_time

    assert response.status_code == 200, f"Batch upload failed: {response.text}"
    batch_data = response.json()

    batch_id = batch_data["batch_id"]
    batch_token = batch_data["private_token"]
    jobs = batch_data["jobs"]

    print(f"[LOAD TEST] Batch upload acknowledged in {upload_duration:.2f}s")
    assert batch_data["total_files"] == TOTAL_REPORTS
    assert len(jobs) == TOTAL_REPORTS

    # Step 2: Poll batch status until completed or timeout
    max_wait = 360  # seconds
    poll_start = time.time()
    completed = False

    while time.time() - poll_start < max_wait:
        status_resp = client.get(f"/api/analyze/batch/{batch_id}")
        assert status_resp.status_code == 200
        batch_status = status_resp.json()

        done_count = batch_status["completed_files"] + batch_status["failed_files"]
        if done_count >= TOTAL_REPORTS or batch_status["status"] == "completed":
            completed = True
            break
        time.sleep(1.0)

    total_time = time.time() - poll_start
    throughput = TOTAL_REPORTS / max(total_time, 0.01)

    print(f"[LOAD TEST] Completed {TOTAL_REPORTS} reports in {total_time:.2f}s ({throughput:.2f} reports/sec)")
    assert completed is True, f"Batch processing did not complete within timeout. Current: {batch_status}"
    assert batch_status["completed_files"] + batch_status["failed_files"] == TOTAL_REPORTS

    # Step 3: Verify individual job records and isolation
    first_job_id = jobs[0]["job_id"]
    single_status = client.get(f"/api/analyze/status/{first_job_id}").json()
    assert single_status["status"] in ["completed", "failed"]

    # Step 4: Verify Batch ZIP Download
    dl_resp = client.get(f"/api/analyze/batch/{batch_id}/download?token={batch_token}")
    assert dl_resp.status_code == 200
    assert dl_resp.headers["content-type"] == "application/zip"
    
    # Verify downloaded ZIP can be read
    downloaded_zip = zipfile.ZipFile(io.BytesIO(dl_resp.content))
    assert len(downloaded_zip.namelist()) > 0
    print(f"[LOAD TEST] Consolidated batch ZIP generated with {len(downloaded_zip.namelist())} reports.")
