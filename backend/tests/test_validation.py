import io
import zipfile
import pytest
from pathlib import Path
from backend.app.core.security import (
    validate_pdf_signature,
    validate_zip_signature,
    safe_extract_zip,
    generate_secure_token,
    hash_token,
    verify_token,
    sanitize_filename
)
from backend.app.core.config import settings

def test_token_generation_and_verification():
    token = generate_secure_token()
    assert len(token) >= 32
    token_hash = hash_token(token)
    assert verify_token(token, token_hash) is True
    assert verify_token("invalid_token_guess", token_hash) is False

def test_sanitize_filename():
    dangerous = "../../etc/passwd/malicious.pdf"
    clean = sanitize_filename(dangerous)
    assert ".." not in clean
    assert "/" not in clean
    assert clean.endswith(".pdf")

def test_validate_pdf_signature(tmp_path: Path):
    # Valid PDF
    valid_pdf = tmp_path / "test_valid.pdf"
    valid_pdf.write_bytes(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF")
    assert validate_pdf_signature(valid_pdf) is True

    # Corrupted / fake PDF (e.g. executable disguised as PDF)
    fake_pdf = tmp_path / "fake.pdf"
    fake_pdf.write_bytes(b"MZ\x90\x00\x03\x00\x00\x00This is an executable")
    assert validate_pdf_signature(fake_pdf) is False

def test_safe_extract_zip(tmp_path: Path):
    zip_path = tmp_path / "test_batch.zip"
    extract_target = tmp_path / "extracted"

    # Create ZIP with valid PDFs and an invalid file
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("report1.pdf", b"%PDF-1.4 sample content 1")
        zf.writestr("nested/report2.pdf", b"%PDF-1.4 sample content 2")
        zf.writestr("malicious.exe", b"malicious executable payload")

    extracted = safe_extract_zip(zip_path, extract_target)
    assert len(extracted) == 2
    for p in extracted:
        assert p.name.endswith(".pdf")
        assert validate_pdf_signature(p) is True

def test_safe_extract_zip_slip_prevention(tmp_path: Path):
    zip_path = tmp_path / "zip_slip.zip"
    extract_target = tmp_path / "safe_dir"
    extract_target.mkdir()

    # Attempt to write outside directory
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("../../../evil.pdf", b"%PDF-1.4 dangerous")

    with pytest.raises(ValueError, match="Malicious path traversal"):
        safe_extract_zip(zip_path, extract_target)
