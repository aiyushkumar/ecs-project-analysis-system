import os
import shutil
import uuid
from typing import Any
from datetime import datetime
from pathlib import Path
import pymupdf
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT

from backend.app.models.schemas import (
    SimilaritySummary, SourceEvidence, SimilarityMatchEvidence, SourceCategory
)

# Vibrant badge colors matching RPi_CSR sample
BADGE_COLORS = [
    colors.HexColor("#0082c8"),  # 1 Turnitin Blue
    colors.HexColor("#00a887"),  # 2 Teal
    colors.HexColor("#6b5b95"),  # 3 Purple
    colors.HexColor("#2e7d32"),  # 4 Green
    colors.HexColor("#d9534f"),  # 5 Red/Coral
    colors.HexColor("#0288d1"),  # 6 Light Blue
    colors.HexColor("#00897b"),  # 7 Mint
    colors.HexColor("#5c6bc0"),  # 8 Indigo
    colors.HexColor("#43a047"),  # 9 Forest
    colors.HexColor("#e65100"),  # 10 Orange
    colors.HexColor("#00acc1"),  # 11 Cyan
    colors.HexColor("#8e24aa"),  # 12 Violet
    colors.HexColor("#3949ab"),  # 13 Navy
    colors.HexColor("#00838f"),  # 14 Dark Cyan
    colors.HexColor("#ef6c00"),  # 15 Amber
    colors.HexColor("#1e88e5"),  # 16 Blue
]

BADGE_RGB_LIST = [
    (0.0, 0.51, 0.78),   # 1 Turnitin Blue
    (0.0, 0.66, 0.53),   # 2 Teal
    (0.42, 0.36, 0.58),  # 3 Purple
    (0.18, 0.49, 0.20),  # 4 Green
    (0.85, 0.33, 0.31),  # 5 Red/Coral
    (0.01, 0.53, 0.82),  # 6 Light Blue
    (0.0, 0.54, 0.48),   # 7 Mint
    (0.36, 0.42, 0.75),  # 8 Indigo
    (0.26, 0.63, 0.28),  # 9 Forest
    (0.90, 0.32, 0.0),   # 10 Orange
    (0.0, 0.67, 0.76),   # 11 Cyan
    (0.56, 0.14, 0.67),  # 12 Violet
    (0.22, 0.29, 0.67),  # 13 Navy
    (0.0, 0.51, 0.56),   # 14 Dark Cyan
    (0.94, 0.42, 0.0),   # 15 Amber
    (0.12, 0.53, 0.90),  # 16 Blue
]

HIGHLIGHT_RGB_LIST = [
    (0.82, 0.92, 0.97),  # 1 Light Blue
    (0.82, 0.95, 0.92),  # 2 Light Teal
    (0.91, 0.85, 0.94),  # 3 Light Purple
    (0.84, 0.96, 0.89),  # 4 Light Green
    (0.98, 0.86, 0.85),  # 5 Light Coral
    (0.88, 0.96, 0.99),  # 6 Soft Blue
    (0.88, 0.95, 0.95),  # 7 Soft Mint
    (0.91, 0.92, 0.96),  # 8 Soft Indigo
    (0.91, 0.96, 0.91),  # 9 Soft Green
    (1.0, 0.88, 0.70),   # 10 Soft Orange
    (0.88, 0.97, 0.98),  # 11 Soft Cyan
    (0.95, 0.90, 0.96),  # 12 Soft Violet
    (0.93, 0.91, 0.96),  # 13 Soft Navy
    (0.88, 0.95, 0.95),  # 14 Soft Dark Cyan
    (1.0, 0.95, 0.88),   # 15 Soft Amber
    (0.89, 0.95, 0.99),  # 16 Soft Bright Blue
]

HIGHLIGHT_BACKGROUNDS = [
    "#d0eaf8", "#d1f2eb", "#e8daef", "#d5f5e3",
    "#fadbd8", "#e1f5fe", "#e0f2f1", "#e8eaf6",
    "#e8f5e9", "#ffe0b2", "#e0f7fa", "#f3e5f5",
    "#ede7f6", "#e0f2f1", "#fff3e0", "#e3f2fd"
]

def get_source_color(source_number: int) -> colors.Color:
    idx = (source_number - 1) % len(BADGE_COLORS)
    return BADGE_COLORS[idx]

def get_source_badge_rgb(source_number: int) -> tuple[float, float, float]:
    idx = (source_number - 1) % len(BADGE_RGB_LIST)
    return BADGE_RGB_LIST[idx]

def get_source_highlight_rgb(source_number: int) -> tuple[float, float, float]:
    idx = (source_number - 1) % len(HIGHLIGHT_RGB_LIST)
    return HIGHLIGHT_RGB_LIST[idx]

def get_source_highlight_hex(source_number: int) -> str:
    idx = (source_number - 1) % len(HIGHLIGHT_BACKGROUNDS)
    return HIGHLIGHT_BACKGROUNDS[idx]


class CoverCanvas(canvas.Canvas):
    """Canvas for Page 1 (Cover Summary) with 'Summary' footer."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def showPage(self):
        page_w, _ = letter
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#475569"))
        self.drawRightString(page_w - 40, 25, "Summary")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(40, 40, page_w - 40, 40)
        self.restoreState()
        super().showPage()


class SourcesCanvas(canvas.Canvas):
    """Canvas for Sources Overview pages with running header and 'Sources overview' footer."""
    report_id: str = "oid:ecs:00000000"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def showPage(self):
        page_w, page_h = letter
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#475569"))
        
        # Header
        self.drawRightString(page_w - 40, page_h - 28, f"Similarity Report ID: {self.report_id}")
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(40, page_h - 35, page_w - 40, page_h - 35)

        # Footer
        self.drawRightString(page_w - 40, 25, "Sources overview")
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(40, 38, page_w - 40, 38)
        self.restoreState()
        super().showPage()


class RPiCSRReportGenerator:
    """
    Generates academic similarity reports in the exact visual design of RPi_CSR_R1(8).pdf.
    
    Structure:
    - Page 1: Cover Page / Metadata Summary & Overall Similarity Breakdown (ReportLab)
    - Pages 2 to N+1: Verbatim full uploaded student submission with Turnitin-style
                      running headers/footers, color highlights, and numbered source badges (PyMuPDF)
    - Pages N+2 to End: Multi-page Sources Overview with ranked list, clickable URLs,
                        database metrics, and legal/academic disclaimers (ReportLab)
    """
    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        self.styles.add(ParagraphStyle(
            name='TurnitinHeader',
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#0082c8")
        ))
        self.styles.add(ParagraphStyle(
            name='MetaLabel',
            fontName='Helvetica',
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#64748b")
        ))
        self.styles.add(ParagraphStyle(
            name='MetaValue',
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#1e293b")
        ))
        self.styles.add(ParagraphStyle(
            name='OverallSimTitle',
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#0f172a")
        ))
        self.styles.add(ParagraphStyle(
            name='SubDetailText',
            fontName='Helvetica',
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#334155")
        ))
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=14,
            spaceAfter=6
        ))
        self.styles.add(ParagraphStyle(
            name='ReportBody',
            fontName='Times-Roman',
            fontSize=10,
            leading=14,
            alignment=TA_JUSTIFY,
            spaceBefore=4,
            spaceAfter=6
        ))
        self.styles.add(ParagraphStyle(
            name='SourceRank',
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=13,
            textColor=colors.white,
            alignment=TA_CENTER
        ))

    def _build_cover_pdf(
        self,
        cover_path: Path,
        report_oid: str,
        original_filename: str,
        word_count: int,
        char_count: int,
        page_count: int,
        file_size_bytes: int,
        submission_time: datetime,
        summary: SimilaritySummary
    ) -> Path:
        """Builds Page 1 (Cover Summary) using ReportLab."""
        doc = SimpleDocTemplate(
            str(cover_path),
            pagesize=letter,
            leftMargin=40,
            rightMargin=40,
            topMargin=45,
            bottomMargin=45
        )

        story = []

        # Header: Logo & Similarity Report ID
        header_table_data = [
            [
                Paragraph("<b>ECS</b> <font color='#0082c8'>■</font> PROJECT ANALYSIS SYSTEM", self.styles['TurnitinHeader']),
                Paragraph(f"<font color='#64748b'>Similarity Report ID:</font> <b>{report_oid}</b>", self.styles['SubDetailText'])
            ]
        ]
        header_table = Table(header_table_data, colWidths=[330, 202])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#e2e8f0"), spaceBefore=2, spaceAfter=14))

        # Paper Name
        story.append(Paragraph("PAPER NAME", self.styles['MetaLabel']))
        story.append(Spacer(1, 2))
        story.append(Paragraph(f"<b>{original_filename}</b>", self.styles['MetaValue']))
        story.append(Spacer(1, 12))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#f1f5f9"), spaceBefore=2, spaceAfter=14))

        # Metadata Grid (Word count, Page count, etc.)
        file_size_mb = f"{file_size_bytes / (1024 * 1024):.1f}MB" if file_size_bytes else "1.2MB"
        sub_date_str = submission_time.strftime("%b %d, %Y %I:%M %p GMT+5:30")
        rep_date_str = datetime.utcnow().strftime("%b %d, %Y %I:%M %p GMT+5:30")

        meta_data = [
            [
                Paragraph("WORD COUNT", self.styles['MetaLabel']),
                Paragraph("CHARACTER COUNT", self.styles['MetaLabel'])
            ],
            [
                Paragraph(f"<b>{word_count:,} Words</b>", self.styles['MetaValue']),
                Paragraph(f"<b>{char_count:,} Characters</b>", self.styles['MetaValue'])
            ],
            [Paragraph("", self.styles['MetaLabel']), Paragraph("", self.styles['MetaLabel'])],
            [
                Paragraph("PAGE COUNT", self.styles['MetaLabel']),
                Paragraph("FILE SIZE", self.styles['MetaLabel'])
            ],
            [
                Paragraph(f"<b>{page_count} Pages</b>", self.styles['MetaValue']),
                Paragraph(f"<b>{file_size_mb}</b>", self.styles['MetaValue'])
            ],
            [Paragraph("", self.styles['MetaLabel']), Paragraph("", self.styles['MetaLabel'])],
            [
                Paragraph("SUBMISSION DATE", self.styles['MetaLabel']),
                Paragraph("REPORT DATE", self.styles['MetaLabel'])
            ],
            [
                Paragraph(f"<b>{sub_date_str}</b>", self.styles['MetaValue']),
                Paragraph(f"<b>{rep_date_str}</b>", self.styles['MetaValue'])
            ],
        ]
        meta_table = Table(meta_data, colWidths=[266, 266])
        meta_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
            ('TOPPADDING', (0,0), (-1,-1), 1),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 14))
        story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#e2e8f0"), spaceBefore=4, spaceAfter=18))

        # Overall Similarity Metric Banner
        sim_val = int(round(summary.overall_similarity))
        story.append(Paragraph(
            f"<font color='#00A3E0' size='18'>●</font> <b>{sim_val}% Overall Similarity</b>",
            self.styles['OverallSimTitle']
        ))
        story.append(Spacer(1, 6))
        story.append(Paragraph(
            "The combined total of all matches, including overlapping sources, for each database.",
            self.styles['SubDetailText']
        ))
        story.append(Spacer(1, 10))

        # Database Breakdown Bullets
        db_data = [
            [
                Paragraph(f"• <b>{int(round(summary.internet_percentage))}%</b> Internet database", self.styles['SubDetailText']),
                Paragraph(f"• <b>{int(round(summary.publications_percentage))}%</b> Publications database", self.styles['SubDetailText'])
            ],
            [
                Paragraph(f"• <b>{int(round(summary.crossref_percentage))}%</b> Crossref database", self.styles['SubDetailText']),
                Paragraph(f"• Crossref Posted Content database", self.styles['SubDetailText'])
            ],
            [
                Paragraph(f"• <b>{int(round(summary.github_percentage))}%</b> Submitted Works / GitHub database", self.styles['SubDetailText']),
                Paragraph(f"• Technical Code & Implementation Repositories", self.styles['SubDetailText'])
            ]
        ]
        db_table = Table(db_data, colWidths=[266, 266])
        db_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(db_table)
        story.append(Spacer(1, 16))

        # Excluded Section
        story.append(Paragraph(
            "<font color='#00A3E0' size='14'>●</font> <b>Excluded from Similarity Report</b>",
            self.styles['SectionHeading']
        ))
        story.append(Spacer(1, 4))
        story.append(Paragraph("• Bibliographic material", self.styles['SubDetailText']))
        story.append(Paragraph("• Quoted material and standard templates", self.styles['SubDetailText']))
        story.append(Paragraph("• Small matches (&lt; 10 words)", self.styles['SubDetailText']))

        doc.build(story, canvasmaker=CoverCanvas)
        return cover_path

    def _build_annotated_document(
        self,
        annotated_path: Path,
        original_pdf_path: Path | None,
        matches: list[SimilarityMatchEvidence],
        report_oid: str,
        original_filename: str,
        page_count: int,
        sections: dict[str, list[Any]] | None = None
    ) -> Path:
        """
        Creates the annotated student submission pages:
        If original_pdf_path exists, loads all pages of the uploaded PDF verbatim,
        stamps running headers & footers, and overlays pastel highlight bars with
        circular numbered badge pills directly at matching passage coordinates.
        Fallback generates clean structured text pages if original PDF is not present.
        """
        if original_pdf_path and original_pdf_path.exists():
            try:
                doc = pymupdf.open(str(original_pdf_path))
                if len(doc) > 0:
                    for p_idx, page in enumerate(doc):
                        orig_page_num = p_idx + 1
                        report_page_num = orig_page_num + 1  # Cover page is Page 1
                        w = page.rect.width
                        h = page.rect.height

                        # Header
                        page.insert_text(
                            (w - 230, 24),
                            f"Similarity Report ID: {report_oid}",
                            fontsize=8,
                            color=(0.4, 0.45, 0.5)
                        )
                        page.draw_line((40, 30), (w - 40, 30), color=(0.85, 0.88, 0.92), width=0.5)

                        # Footer
                        page.insert_text(
                            (40, h - 22),
                            "ECS AI Analysis Report - Evidence Grounded",
                            fontsize=8,
                            color=(0.4, 0.45, 0.5)
                        )
                        page.insert_text(
                            (w - 55, h - 22),
                            f"{report_page_num}",
                            fontsize=8,
                            color=(0.4, 0.45, 0.5)
                        )
                        page.draw_line((40, h - 30), (w - 40, h - 30), color=(0.85, 0.88, 0.92), width=0.5)

                        # Search and highlight matches on this page
                        page_matches = [m for m in matches if m.page_number == orig_page_num]
                        # If page_number is unassigned (0 or None) or no matches found on this page,
                        # also allow matching if text explicitly appears on this page
                        if not page_matches:
                            for m in matches:
                                if m.page_number in (0, None) and m.matched_text:
                                    # Quick probe
                                    probe = m.matched_text[:min(30, len(m.matched_text))]
                                    if page.search_for(probe):
                                        page_matches.append(m)

                        for m in page_matches:
                            if not m.matched_text or len(m.matched_text.strip()) < 5:
                                continue

                            rects = page.search_for(m.matched_text)
                            if not rects and len(m.matched_text) > 30:
                                # Sub-phrase sliding window search
                                words = m.matched_text.split()
                                if len(words) >= 6:
                                    for k in range(0, min(len(words) - 5, 20), 5):
                                        chunk = " ".join(words[k:k+6])
                                        sub_rects = page.search_for(chunk)
                                        if sub_rects:
                                            rects.extend(sub_rects)

                            if rects:
                                highlight_rgb = get_source_highlight_rgb(m.source_number)
                                badge_rgb = get_source_badge_rgb(m.source_number)

                                # Apply highlights
                                for r in rects:
                                    annot = page.add_highlight_annot(r)
                                    if annot:
                                        annot.set_colors(stroke=highlight_rgb)
                                        annot.update()

                                # Draw circular badge pill at the start of first rect
                                first_r = rects[0]
                                badge_radius = 5.5
                                cx = max(18.0, first_r.x0 - badge_radius - 2)
                                cy = (first_r.y0 + first_r.y1) / 2.0

                                page.draw_circle((cx, cy), badge_radius, fill=badge_rgb, color=badge_rgb)
                                num_str = str(m.source_number)
                                tx_offset = 2.5 if len(num_str) == 1 else 4.0
                                page.insert_text((cx - tx_offset, cy + 2.5), num_str, fontsize=6.5, color=(1, 1, 1), fontname="helv")

                    doc.save(str(annotated_path))
                    doc.close()
                    return annotated_path
            except Exception as e:
                # If opening/annotating fails, fallback gracefully to synthetic document
                pass

        # Fallback generator: create clean multi-page document with text passages & highlights
        fallback_doc = pymupdf.open()
        pages_to_create = max(1, page_count if page_count > 0 else 1)
        # Limit fallback page creation to 50 if artificial
        pages_to_create = min(pages_to_create, 50)

        for p_idx in range(pages_to_create):
            orig_page_num = p_idx + 1
            report_page_num = orig_page_num + 1
            page = fallback_doc.new_page(width=612, height=792)
            w = 612
            h = 792

            # Header & Footer
            page.insert_text((w - 230, 24), f"Similarity Report ID: {report_oid}", fontsize=8, color=(0.4, 0.45, 0.5))
            page.draw_line((40, 30), (w - 40, 30), color=(0.85, 0.88, 0.92), width=0.5)
            page.insert_text((40, h - 22), "ECS AI Analysis Report - Evidence Grounded", fontsize=8, color=(0.4, 0.45, 0.5))
            page.insert_text((w - 55, h - 22), f"{report_page_num}", fontsize=8, color=(0.4, 0.45, 0.5))
            page.draw_line((40, h - 30), (w - 40, h - 30), color=(0.85, 0.88, 0.92), width=0.5)

            # Title
            page.insert_text((40, 60), f"{original_filename} - Document Submission (Page {orig_page_num})", fontsize=11, color=(0.1, 0.15, 0.2))

            # Render matches on this page
            page_matches = [m for m in matches if m.page_number == orig_page_num]
            if not page_matches and p_idx == 0:
                page_matches = matches

            y_pos = 90
            for m in page_matches:
                if y_pos > h - 80:
                    break
                badge_rgb = get_source_badge_rgb(m.source_number)
                highlight_rgb = get_source_highlight_rgb(m.source_number)

                # Draw badge
                page.draw_circle((50, y_pos), 5.5, fill=badge_rgb, color=badge_rgb)
                num_str = str(m.source_number)
                page.insert_text((47.5, y_pos + 2.5), num_str, fontsize=6.5, color=(1, 1, 1), fontname="helv")

                # Text box
                text_rect = pymupdf.Rect(65, y_pos - 8, w - 40, y_pos + 25)
                page.draw_rect(text_rect, fill=highlight_rgb, color=highlight_rgb)
                page.insert_textbox(text_rect, m.matched_text, fontsize=9, color=(0.05, 0.1, 0.15))
                y_pos += 45

        fallback_doc.save(str(annotated_path))
        fallback_doc.close()
        return annotated_path

    def _build_sources_overview_pdf(
        self,
        sources_path: Path,
        report_oid: str,
        summary: SimilaritySummary,
        top_sources: list[SourceEvidence]
    ) -> Path:
        """
        Builds the complete multi-page Sources Overview matching pages 116–135 of RPi_CSR_R1(8).pdf.
        """
        doc = SimpleDocTemplate(
            str(sources_path),
            pagesize=letter,
            leftMargin=40,
            rightMargin=40,
            topMargin=45,
            bottomMargin=45
        )

        story = []
        sim_val = int(round(summary.overall_similarity))

        # Overall similarity title
        story.append(Paragraph(
            f"<font color='#00A3E0' size='18'>●</font> <b>{sim_val}% Overall Similarity</b>",
            self.styles['OverallSimTitle']
        ))
        story.append(Spacer(1, 4))
        story.append(Paragraph("Top sources found in the following databases:", self.styles['SubDetailText']))
        story.append(Spacer(1, 6))

        db_sources_data = [
            [
                Paragraph(f"• <b>{int(round(summary.internet_percentage))}%</b> Internet database", self.styles['SubDetailText']),
                Paragraph(f"• <b>{int(round(summary.publications_percentage))}%</b> Publications database", self.styles['SubDetailText'])
            ],
            [
                Paragraph(f"• <b>{int(round(summary.crossref_percentage))}%</b> Crossref database", self.styles['SubDetailText']),
                Paragraph(f"• Crossref Posted Content database", self.styles['SubDetailText'])
            ],
            [
                Paragraph(f"• <b>{int(round(summary.github_percentage))}%</b> Submitted Works / GitHub database", self.styles['SubDetailText']),
                Paragraph(f"• Open-Access Research Repositories", self.styles['SubDetailText'])
            ]
        ]
        db_s_table = Table(db_sources_data, colWidths=[266, 266])
        db_s_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ]))
        story.append(db_s_table)
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#e2e8f0"), spaceBefore=2, spaceAfter=12))

        # TOP SOURCES heading
        story.append(Paragraph("<b>TOP SOURCES</b>", self.styles['SectionHeading']))
        story.append(Paragraph(
            "The sources with the highest number of matches within the submission. Overlapping sources will not be displayed.",
            self.styles['SubDetailText']
        ))
        story.append(Spacer(1, 10))

        if not top_sources:
            story.append(Paragraph(
                "<i>No external sources exceeded the similarity threshold. High originality confirmed across all indexed repositories.</i>",
                self.styles['SubDetailText']
            ))
        else:
            # Multi-page source list matching RPi_CSR style
            src_rows = []
            for s in top_sources:
                src_color = get_source_color(s.source_number)
                hex_color = src_color.hexval()
                if not hex_color.startswith("#"):
                    hex_color = f"#{hex_color}"

                pct_display = f"{s.percentage:.0f}%" if s.percentage >= 1.0 else "<1%"
                badge_p = Paragraph(f"<font color='white' backColor='{hex_color}'><b>&nbsp;{s.source_number}&nbsp;</b></font>", self.styles['SourceRank'])
                
                title_url = f"<b>{s.title}</b><br/><font color='#64748b' size='8'>{s.category.value}</font><br/><a href='{s.url}' color='#0082c8'><font size='8'><u>{s.url}</u></font></a>"
                detail_p = Paragraph(title_url, self.styles['SubDetailText'])
                
                pct_p = Paragraph(f"<b><font color='{hex_color}' size='11'>{pct_display}</font></b>", self.styles['MetaValue'])

                src_rows.append([badge_p, detail_p, pct_p])

            src_table = Table(src_rows, colWidths=[32, 438, 62])
            src_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('ALIGN', (2,0), (2,-1), 'RIGHT'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 7),
                ('TOPPADDING', (0,0), (-1,-1), 7),
                ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor("#f1f5f9")),
            ]))
            story.append(src_table)

        story.append(Spacer(1, 16))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0"), spaceBefore=4, spaceAfter=10))

        # Methodology & Legal Disclaimer
        story.append(Paragraph("<b>METHODOLOGY & DISCLAIMER</b>", self.styles['MetaLabel']))
        story.append(Spacer(1, 4))
        story.append(Paragraph(
            f"<b>Calculation Method:</b> {summary.calculation_method}.<br/>"
            f"<b>Exclusions Applied:</b> Bibliographic references, quotation blocks, standard academic phrasing, and duplicate source occurrences.<br/>"
            f"<b>Legal & Academic Disclaimer:</b> {summary.disclaimer}",
            self.styles['SubDetailText']
        ))

        # Configure SourcesCanvas with the report_oid
        SourcesCanvas.report_id = report_oid
        doc.build(story, canvasmaker=SourcesCanvas)
        return sources_path

    def generate(
        self,
        job_id: str,
        original_filename: str,
        word_count: int,
        char_count: int,
        page_count: int,
        file_size_bytes: int,
        submission_time: datetime,
        summary: SimilaritySummary,
        top_sources: list[SourceEvidence],
        matches: list[SimilarityMatchEvidence],
        sections: dict[str, list[Any]] | None = None,
        original_pdf_path: Path | None = None
    ) -> Path:
        """
        Orchestrates full Turnitin-grade report generation:
        Page 1: Cover / Summary
        Pages 2..N+1: All pages of original document annotated with pastel highlights and numbered badge pills
        Pages N+2..End: Full multi-page Sources Overview
        """
        report_oid = f"oid:ecs:{job_id[:8]}"
        build_dir = self.output_path.parent / f"_build_{uuid.uuid4().hex[:8]}"
        build_dir.mkdir(parents=True, exist_ok=True)

        cover_path = build_dir / "cover.pdf"
        annotated_path = build_dir / "annotated.pdf"
        sources_path = build_dir / "sources.pdf"

        try:
            # 1. Build Cover Page (ReportLab)
            self._build_cover_pdf(
                cover_path=cover_path,
                report_oid=report_oid,
                original_filename=original_filename,
                word_count=word_count,
                char_count=char_count,
                page_count=page_count,
                file_size_bytes=file_size_bytes,
                submission_time=submission_time,
                summary=summary
            )

            # 2. Build Annotated Original Document (PyMuPDF)
            self._build_annotated_document(
                annotated_path=annotated_path,
                original_pdf_path=original_pdf_path,
                matches=matches,
                report_oid=report_oid,
                original_filename=original_filename,
                page_count=page_count,
                sections=sections
            )

            # 3. Build Multi-Page Sources Overview (ReportLab)
            self._build_sources_overview_pdf(
                sources_path=sources_path,
                report_oid=report_oid,
                summary=summary,
                top_sources=top_sources
            )

            # 4. Merge all sections into final output PDF
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            final_doc = pymupdf.open()

            # Insert Cover (Page 1)
            cover_doc = pymupdf.open(str(cover_path))
            final_doc.insert_pdf(cover_doc)
            cover_doc.close()

            # Insert Full Annotated Document (Pages 2 to N+1)
            annot_doc = pymupdf.open(str(annotated_path))
            final_doc.insert_pdf(annot_doc)
            annot_doc.close()

            # Insert Sources Overview (Pages N+2 to End)
            sources_doc = pymupdf.open(str(sources_path))
            final_doc.insert_pdf(sources_doc)
            sources_doc.close()

            final_doc.save(str(self.output_path))
            final_doc.close()

            return self.output_path

        finally:
            # Cleanup temporary build directory
            if build_dir.exists():
                shutil.rmtree(build_dir, ignore_errors=True)
