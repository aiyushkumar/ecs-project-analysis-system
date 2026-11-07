import pytest
from pathlib import Path
from backend.app.pdf_processing.extractor import extract_pdf_document, is_code_block
from backend.app.pdf_processing.segmenter import segment_report

def test_code_block_detector():
    code_sample = """
    import numpy as np
    def calculate_metrics(y_true, y_pred):
        diff = y_true - y_pred
        return np.mean(diff ** 2)
    """
    assert is_code_block(code_sample) is True

    prose_sample = """
    This project introduces an artificial intelligence system designed to detect similarities
    across various academic and open source repositories.
    """
    assert is_code_block(prose_sample) is False

def test_extract_and_segment_pdf():
    sample_pdf = Path("samples/sample_project_report.pdf")
    assert sample_pdf.exists(), "Sample input PDF must exist for extraction test"

    doc = extract_pdf_document(sample_pdf)
    assert doc.page_count >= 1
    assert doc.word_count > 50
    assert doc.char_count > 200
    assert len(doc.blocks) > 0

    segmented = segment_report(doc)
    assert len(segmented.all_passages) > 0
    # Abstract or Introduction detected
    detected_lower = [s.lower() for s in segmented.detected_section_names]
    assert any("abstract" in s or "intro" in s or "general" in s for s in detected_lower)
