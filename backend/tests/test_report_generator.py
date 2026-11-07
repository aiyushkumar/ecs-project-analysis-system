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
