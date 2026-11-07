import io
import logging
import re
from pathlib import Path
from typing import Any
from PIL import Image
import pymupdf  # PyMuPDF
import pdfplumber

from backend.app.pdf_processing.ocr import is_ocr_available, extract_text_from_image

logger = logging.getLogger(__name__)

CODE_INDICATORS = [
    r'^\s*def\s+\w+\s*\(',
    r'^\s*class\s+\w+\s*[:\(]',
    r'^\s*import\s+\w+',
    r'^\s*from\s+\w+\s+import',
    r'^\s*#include\s*<',
    r'^\s*public\s+class\s+\w+',
    r'^\s*function\s+\w+\s*\(',
    r'^\s*const\s+\w+\s*=',
    r'^\s*var\s+\w+\s*=',
    r'^\s*let\s+\w+\s*=',
    r'^\s*for\s*\(.+;.+;.+\)',
    r'^\s*while\s*\(.+\)',
    r'[{};]\s*$',
]

def is_code_block(text: str) -> bool:
    """Heuristic to detect if a text block contains programming code."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if not lines:
        return False
    
    code_matches = 0
    for line in lines:
        for pattern in CODE_INDICATORS:
            if re.search(pattern, line):
                code_matches += 1
                break
    
    # If more than 30% lines match programming syntax or contains braces and semicolons
    brace_semi_count = text.count("{") + text.count("}") + text.count(";")
    if code_matches >= 2 or (brace_semi_count >= 3 and len(lines) <= 15):
        return True
    return False

class ExtractedBlock:
    def __init__(self, text: str, page_num: int, bbox: tuple[float, float, float, float], is_code: bool = False):
        self.text = text.strip()
        self.page_num = page_num
        self.bbox = bbox  # (x0, y0, x1, y1)
        self.is_code = is_code

class ExtractedDocument:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.filename = file_path.name
        self.file_size_bytes = file_path.stat().st_size
        self.page_count: int = 0
        self.word_count: int = 0
        self.char_count: int = 0
        self.full_text: str = ""
        self.page_texts: dict[int, str] = {}
        self.blocks: list[ExtractedBlock] = []
        self.tables: list[dict] = []
        self.scanned_pages: list[int] = []
        self.references_text: str = ""
        self.code_blocks: list[dict] = []

def extract_pdf_document(file_path: Path) -> ExtractedDocument:
    """
    Extracts text, blocks, tables, code fragments, and coordinates from a PDF document.
    Handles scanned pages with OCR fallback.
    """
    doc_info = ExtractedDocument(file_path)
    
    try:
        pdf_doc = pymupdf.open(str(file_path))
        doc_info.page_count = len(pdf_doc)
        
        all_text_parts = []
        
        for page_idx in range(len(pdf_doc)):
            page_num = page_idx + 1
            page = pdf_doc[page_idx]
            
            # Extract standard text blocks with bounding boxes
            # get_text("blocks") returns tuples: (x0, y0, x1, y1, "text", block_no, block_type)
            page_blocks = page.get_text("blocks")
            page_text_accum = []
            
            has_text = False
            for b in page_blocks:
                # type 0 means text
                if len(b) >= 5 and b[6] == 0 if len(b) > 6 else True:
                    b_text = str(b[4]).strip()
                    if b_text:
                        has_text = True
                        bbox = (float(b[0]), float(b[1]), float(b[2]), float(b[3]))
                        code_flag = is_code_block(b_text)
                        doc_info.blocks.append(ExtractedBlock(b_text, page_num, bbox, is_code=code_flag))
                        page_text_accum.append(b_text)
                        if code_flag:
                            doc_info.code_blocks.append({
                                "page_num": page_num,
                                "bbox": bbox,
                                "code": b_text
                            })
            
            # Detect scanned page (if page has images and minimal text)
            if not has_text or len(" ".join(page_text_accum)) < 40:
                # Check for images on page
                images = page.get_images()
                if images:
                    doc_info.scanned_pages.append(page_num)
                    # Attempt OCR on scanned page
                    if is_ocr_available():
                        pix = page.get_pixmap()
                        img = Image.open(io.BytesIO(pix.tobytes("png")))
                        ocr_text = extract_text_from_image(img).strip()
                        if ocr_text:
                            page_text_accum.append(ocr_text)
                            rect = page.rect
                            doc_info.blocks.append(
                                ExtractedBlock(ocr_text, page_num, (rect.x0, rect.y0, rect.x1, rect.y1), False)
                            )
            
            combined_page_text = "\n".join(page_text_accum)
            doc_info.page_texts[page_num] = combined_page_text
            all_text_parts.append(combined_page_text)
        
        pdf_doc.close()
        
        doc_info.full_text = "\n\n".join(all_text_parts)
        doc_info.word_count = len(re.findall(r'\b\w+\b', doc_info.full_text))
        doc_info.char_count = len(doc_info.full_text)
        
        # Extract tables where practical using pdfplumber
        try:
            with pdfplumber.open(str(file_path)) as plumber_pdf:
                for idx, page in enumerate(plumber_pdf.pages):
                    page_tables = page.extract_tables()
                    for t in page_tables:
                        if t and len(t) > 1:
                            doc_info.tables.append({
                                "page_num": idx + 1,
                                "rows": t
                            })
        except Exception as e:
            logger.debug(f"pdfplumber table extraction info: {e}")
            
    except Exception as e:
        logger.error(f"Failed to extract PDF {file_path}: {e}")
        raise ValueError(f"Could not parse PDF file {file_path.name}: {str(e)}")

    return doc_info
