import logging
from pathlib import Path
from PIL import Image

logger = logging.getLogger(__name__)

# Check if Tesseract is installed and available
_tesseract_available = False
try:
    import pytesseract
    # Try a quick version check or find_tesseract
    pytesseract.get_tesseract_version()
    _tesseract_available = True
    logger.info("Tesseract OCR is available and active.")
except Exception as e:
    logger.warning("Tesseract OCR binary not found in system PATH. Image-based OCR fallback active.")
    _tesseract_available = False

def is_ocr_available() -> bool:
    return _tesseract_available

def extract_text_from_image(image: Image.Image) -> str:
    """
    Extract text from a PIL Image. If Tesseract is available, runs OCR;
    otherwise returns an empty string or basic message without raising an unhandled exception.
    """
    if not _tesseract_available:
        return ""
    try:
        import pytesseract
        return pytesseract.image_to_string(image)
    except Exception as e:
        logger.error(f"OCR extraction failed on image: {e}")
        return ""
