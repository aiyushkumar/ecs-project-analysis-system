import hashlib
import os
import re
import secrets
from pathlib import Path
import zipfile

def generate_secure_token() -> str:
    """Generate cryptographically secure 32-byte URL-safe private token."""
    return secrets.token_urlsafe(32)

def hash_token(token: str) -> str:
    """Hash private token with SHA-256 for secure storage."""
    return hashlib.sha256(token.encode('utf-8')).hexdigest()

def verify_token(raw_token: str, hashed_token: str) -> bool:
    """Verify raw token against stored SHA-256 hash in constant time."""
    computed = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
    return secrets.compare_digest(computed, hashed_token)

def compute_file_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and shell injection."""
    clean = os.path.basename(filename)
    clean = re.sub(r'[^a-zA-Z0-9_\-\. ]', '_', clean)
    clean = clean.strip()
    return clean or "document.pdf"

def validate_pdf_signature(file_path: Path) -> bool:
    """
    Validate magic bytes for PDF format.
    Standard PDFs must begin with '%PDF-'.
    """
    try:
        with open(file_path, "rb") as f:
            header = f.read(1024)
            # %PDF- is typically at offset 0, but some tools allow a small preamble
            return b"%PDF-" in header[:1024]
    except Exception:
        return False

def validate_zip_signature(file_path: Path) -> bool:
    """
    Validate magic bytes for ZIP format.
    ZIP archives start with 'PK\x03\x04'.
    """
    try:
        with open(file_path, "rb") as f:
            header = f.read(4)
            return header.startswith(b"PK\x03\x04") or header.startswith(b"PK\x05\x06")
    except Exception:
        return False

def safe_extract_zip(zip_path: Path, target_dir: Path) -> list[Path]:
    """
    Extracts only PDF files from a ZIP archive safely, preventing Zip Slip path traversal.
    """
    extracted_pdfs: list[Path] = []
    target_dir.mkdir(parents=True, exist_ok=True)
    resolved_target = target_dir.resolve()

    with zipfile.ZipFile(zip_path, 'r') as zf:
        for member in zf.infolist():
            # Skip directories or macOS hidden metadata
            if member.is_dir() or member.filename.startswith("__MACOSX/") or os.path.basename(member.filename).startswith("._"):
                continue

            # Ensure file ends with .pdf
            if not member.filename.lower().endswith(".pdf"):
                continue

            # Prevent Zip Slip: check target path is strictly within resolved_target
            dest_path = (resolved_target / member.filename).resolve()
            if not str(dest_path).startswith(str(resolved_target)):
                raise ValueError(f"Malicious path traversal detected in ZIP entry: {member.filename}")

            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as source, open(dest_path, "wb") as target:
                while chunk := source.read(65536):
                    target.write(chunk)

            # Validate extracted file is a genuine PDF
            if validate_pdf_signature(dest_path):
                extracted_pdfs.append(dest_path)
            else:
                dest_path.unlink(missing_ok=True)

    return extracted_pdfs
