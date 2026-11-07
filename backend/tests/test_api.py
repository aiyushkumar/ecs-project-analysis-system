import io
import time
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_upload_invalid_file():
    fake_file = io.BytesIO(b"This is a plain text file, not a valid PDF")
    response = client.post(
        "/api/analyze/upload",
        files=[("files", ("test.txt", fake_file, "text/plain"))]
    )
    assert response.status_code == 400

def test_single_upload_and_status():
    # Valid minimal PDF
    pdf_bytes = b"%PDF-1.4\n1 0 obj\n<< /Title (Test Project) >>\nendobj\ntrailer\n<<>>\n%%EOF"
    pdf_file = io.BytesIO(pdf_bytes)

    response = client.post(
        "/api/analyze/upload",
        files=[("files", ("test_project.pdf", pdf_file, "application/pdf"))]
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    job = data[0]
    assert "job_id" in job
    assert "private_token" in job
    assert job["status"] == "pending"

    job_id = job["job_id"]
    token = job["private_token"]

    # Check status endpoint
    status_resp = client.get(f"/api/analyze/status/{job_id}")
    assert status_resp.status_code == 200
    assert status_resp.json()["job_id"] == job_id

    # Check unauthorized result access
    res_unauth = client.get(f"/api/analyze/result/{job_id}")
    assert res_unauth.status_code == 401

    # Check wrong token
    res_forbidden = client.get(f"/api/analyze/result/{job_id}?token=wrong_token_guess")
    assert res_forbidden.status_code == 403
