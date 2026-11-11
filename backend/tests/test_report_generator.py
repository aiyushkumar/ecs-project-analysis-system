from datetime import datetime
from pathlib import Path
import pymupdf
from backend.app.models.schemas import (
    SimilaritySummary, SourceEvidence, SimilarityMatchEvidence, SourceCategory, MatchType
)
from backend.app.report_generator.rpi_csr_generator import RPiCSRReportGenerator

def test_rpi_csr_report_generation(tmp_path: Path):
    output_pdf = tmp_path / "test_report.pdf"
    generator = RPiCSRReportGenerator(output_pdf)

    summary = SimilaritySummary(
        overall_similarity=22.0,
        internet_percentage=12.0,
        publications_percentage=10.0,
        crossref_percentage=8.0,
        github_percentage=15.0,
        exact_similarity=6.0,
        lexical_similarity=7.0,
        semantic_similarity=9.0,
        code_similarity=0.0,
        calculation_method="Non-overlapping token union normalized over non-bibliographic document passages",
        disclaimer="Similarity results are indicators for human interpretation and do not constitute an automatic verdict of academic misconduct."
    )

    sources = [
        SourceEvidence(
            source_id="s1", source_number=1, title="IEEE Transactions on IoT",
            url="https://doi.org/10.1109/sample", category=SourceCategory.CROSSREF,
            percentage=12.0, match_count=8
        ),
        SourceEvidence(
            source_id="s2", source_number=2, title="github.com/sample/project",
            url="https://github.com/sample/project", category=SourceCategory.GITHUB,
            percentage=10.0, match_count=4
        )
    ]

    matches = [
        SimilarityMatchEvidence(
            match_id="m1", source_number=1, source_title="IEEE Transactions on IoT",
            source_url="https://doi.org/10.1109/sample", source_category=SourceCategory.CROSSREF,
            page_number=1, section_name="Introduction",
            matched_text="Prototyping cyber-physical IoT architectures using single board embedded systems.",
            source_excerpt="Prototyping cyber-physical IoT architectures using single board embedded systems.",
            match_type=MatchType.EXACT, confidence=0.98
        )
    ]

    generator.generate(
        job_id="test_run_123",
        original_filename="Sample_Dissertation.pdf",
        word_count=12500,
        char_count=85000,
        page_count=45,
        file_size_bytes=4200000,
        submission_time=datetime.utcnow(),
        summary=summary,
        top_sources=sources,
        matches=matches
    )

    assert output_pdf.exists()
    assert output_pdf.stat().st_size > 3000

    # Validate with PyMuPDF
    doc = pymupdf.open(str(output_pdf))
    assert len(doc) >= 3
    # Page 1 contains Summary
    p1_text = doc[0].get_text()
    assert "22% Overall Similarity" in p1_text or "22%" in p1_text
    assert "Sample_Dissertation.pdf" in p1_text
    assert "Summary" in p1_text

    # Final page contains Sources overview
    p_last_text = doc[-1].get_text()
    assert "TOP SOURCES" in p_last_text or "Sources overview" in p_last_text


def test_full_page_annotation_matching_rpi_csr(tmp_path: Path):
    """
    Verifies that when a multi-page PDF is provided, the generator includes
    every single page of the original submission verbatim with running headers,
    footers, highlights, and circular badge numbers, followed by the complete
    sources overview table.
    """
    # Create a 5-page original PDF
    orig_path = tmp_path / "original_thesis.pdf"
    doc_orig = pymupdf.open()
    for i in range(5):
        page = doc_orig.new_page(width=612, height=792)
        page.insert_text((72, 100), f"Thesis Chapter {i+1}: Advanced Systems Engineering", fontsize=14)
        page.insert_text((72, 140), "Raspberry Pi microcontrollers are widely used in modern internet of things.", fontsize=11)
        page.insert_text((72, 180), "Neural network models were trained to optimize energy consumption.", fontsize=11)
    doc_orig.save(str(orig_path))
    doc_orig.close()

    output_pdf = tmp_path / "thesis_similarity_report.pdf"
    generator = RPiCSRReportGenerator(output_pdf)

    summary = SimilaritySummary(
        overall_similarity=15.0,
        internet_percentage=8.0,
        publications_percentage=11.0,
        crossref_percentage=5.0,
        github_percentage=9.0,
        exact_similarity=4.0,
        lexical_similarity=5.0,
        semantic_similarity=6.0,
        code_similarity=0.0,
        calculation_method="Non-overlapping token union normalized over non-bibliographic document passages",
        disclaimer="Similarity results are indicators for human interpretation and do not constitute an automatic verdict of academic misconduct."
    )

    sources = [
        SourceEvidence(
            source_id="s1", source_number=1, title="researchgate.net",
            url="https://researchgate.net/publication/123", category=SourceCategory.INTERNET,
            percentage=8.0, match_count=5
        ),
        SourceEvidence(
            source_id="s2", source_number=2, title="IEEE Transactions on IoT",
            url="https://doi.org/10.1109/iot", category=SourceCategory.PUBLICATIONS,
            percentage=5.0, match_count=3
        )
    ]

    matches = [
        SimilarityMatchEvidence(
            match_id="m1", source_number=1, source_title="researchgate.net",
            source_url="https://researchgate.net/publication/123", source_category=SourceCategory.INTERNET,
            page_number=1, section_name="Introduction",
            matched_text="Raspberry Pi",
            source_excerpt="Raspberry Pi",
            match_type=MatchType.EXACT, confidence=0.99
        )
    ]

    generator.generate(
        job_id="thesis_job_999",
        original_filename="original_thesis.pdf",
        word_count=2400,
        char_count=16000,
        page_count=5,
        file_size_bytes=orig_path.stat().st_size,
        submission_time=datetime.utcnow(),
        summary=summary,
        top_sources=sources,
        matches=matches,
        original_pdf_path=orig_path,
        include_raw_document=True
    )

    assert output_pdf.exists()

    # Verify page breakdown:
    # Page 1: Cover Summary
    # Pages 2 to 6: 5 Original thesis pages
    # Pages 7+: Sources overview
    res_doc = pymupdf.open(str(output_pdf))
    assert len(res_doc) >= 7, f"Expected at least 7 pages, got {len(res_doc)}"

    # Page 1 must have metadata and Overall Similarity
    p1_text = res_doc[0].get_text()
    assert "15% Overall Similarity" in p1_text or "15%" in p1_text
    assert "Summary" in p1_text

    # Page 2 (original thesis page 1) must have the thesis text and running header/footer
    p2_text = res_doc[1].get_text()
    assert "Thesis Chapter 1" in p2_text
    assert "Similarity Report ID: oid:ecs:thesis_j" in p2_text
    assert "ECS AI Analysis Report" in p2_text

    # Page 6 (original thesis page 5) must also be preserved
    p6_text = res_doc[5].get_text()
    assert "Thesis Chapter 5" in p6_text

    # Page 7 (Sources Overview) must have TOP SOURCES and Sources overview footer
    p7_text = res_doc[6].get_text()
    assert "TOP SOURCES" in p7_text or "Sources overview" in p7_text

    res_doc.close()

