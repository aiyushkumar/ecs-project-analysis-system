import os
from typing import Any
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY

from backend.app.models.schemas import (
    SimilaritySummary, SourceEvidence, SimilarityMatchEvidence, SourceCategory
)

# Palette matching RPi_CSR sample
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

HIGHLIGHT_BACKGROUNDS = [
    "#d0eaf8",  # 1
    "#d1f2eb",  # 2
    "#e8daef",  # 3
    "#d5f5e3",  # 4
    "#fadbd8",  # 5
    "#e1f5fe",  # 6
    "#e0f2f1",  # 7
    "#e8eaf6",  # 8
    "#e8f5e9",  # 9
    "#ffe0b2",  # 10
    "#e0f7fa",  # 11
    "#f3e5f5",  # 12
    "#ede7f6",  # 13
    "#e0f2f1",  # 14
    "#fff3e0",  # 15
    "#e3f2fd",  # 16
]

def get_source_color(source_number: int) -> colors.Color:
    idx = (source_number - 1) % len(BADGE_COLORS)
    return BADGE_COLORS[idx]

def get_source_highlight_hex(source_number: int) -> str:
    idx = (source_number - 1) % len(HIGHLIGHT_BACKGROUNDS)
    return HIGHLIGHT_BACKGROUNDS[idx]

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute total pages and render
    RPi_CSR-style headers and footers.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#475569"))

        page_w, page_h = letter
        current_page = self._pageNumber

        # Cover page footer
        if current_page == 1:
            self.drawRightString(page_w - 40, 25, "Summary")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(40, 40, page_w - 40, 40)
        else:
            # Header on later pages
            report_id = getattr(self, "report_id", "oid:3618:58198888")
            self.drawRightString(page_w - 40, page_h - 28, f"Similarity Report ID: {report_id}")
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(40, page_h - 35, page_w - 40, page_h - 35)

            # Footer
            is_sources_page = getattr(self, "sources_page_start", 999999) <= current_page
            if is_sources_page:
                self.drawRightString(page_w - 40, 25, "Sources overview")
            else:
                self.drawString(40, 25, "ECS AI Analysis Report — Evidence Grounded")
                self.drawRightString(page_w - 40, 25, f"{current_page}")

            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(40, 38, page_w - 40, 38)

        self.restoreState()


class RPiCSRReportGenerator:
    """
    Generates academic similarity reports in the exact visual design of RPi_CSR_R1(8).pdf.
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
        sections: dict[str, list[Any]] | None = None
    ):
        doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=letter,
            leftMargin=40,
            rightMargin=40,
            topMargin=45,
            bottomMargin=45
        )

        story = []
        report_oid = f"ecs:{job_id[:8]}"

        # =========================================================================
        # PAGE 1 — COVER / SUMMARY (RPi_CSR Exact Layout)
        # =========================================================================
        
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
        
        story.append(PageBreak())

        # =========================================================================
        # PAGES 2 ONWARD — HIGHLIGHTED CONTENT (RPi_CSR Matching Style)
        # =========================================================================
        story.append(Paragraph("<b>Highlights & Page-Wise Similarity Analysis</b>", self.styles['TurnitinHeader']))
        story.append(Spacer(1, 4))
        story.append(Paragraph(
            f"<b>{original_filename}</b> — Showing matched passages with source indices.",
            self.styles['SubDetailText']
        ))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0"), spaceBefore=2, spaceAfter=14))

        if not matches:
            story.append(Paragraph(
                "<i>No significant matching passages were identified within the searched databases. All analyzed sections demonstrate high novelty and originality.</i>",
                self.styles['ReportBody']
            ))
            story.append(Spacer(1, 20))
        else:
            # Group matches by page and section
            matches_by_page: dict[int, list[SimilarityMatchEvidence]] = {}
            for m in matches:
                matches_by_page.setdefault(m.page_number, []).append(m)

            for page_num in sorted(matches_by_page.keys()):
                page_matches = matches_by_page[page_num]
                story.append(Paragraph(f"<b>[Report Page {page_num}]</b>", self.styles['SectionHeading']))
                story.append(Spacer(1, 4))

                for m in page_matches:
                    bg_color = get_source_highlight_hex(m.source_number)
                    src_col = get_source_color(m.source_number)
                    hex_color = src_col.hexval()
                    if not hex_color.startswith("#"):
                        hex_color = f"#{hex_color}"

                    # Turnitin badge: <font color="white" backColor="#0082c8"><b> 1 </b></font>
                    badge_html = f"<font color='white' backColor='{hex_color}'><b> {m.source_number} </b></font>"
                    highlighted_text = f"<font backColor='{bg_color}'>{m.matched_text}</font>"
                    
                    passage_p = Paragraph(f"{badge_html} {highlighted_text}", self.styles['ReportBody'])
                    
                    evidence_table_data = [
                        [passage_p],
                        [Paragraph(
                            f"<font color='#64748b' size='8'>Source #{m.source_number} ({m.source_category.value}) — <b>{m.source_title}</b> | Match: {m.match_type.value} ({int(m.confidence*100)}%)<br/>URL: <a href='{m.source_url}' color='#0082c8'><u>{m.source_url}</u></a></font>",
                            self.styles['SubDetailText']
                        )]
                    ]
                    ev_table = Table(evidence_table_data, colWidths=[532])
                    ev_table.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,0), colors.HexColor(bg_color)),
                        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#f8fafc")),
                        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
                        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
                        ('TOPPADDING', (0,0), (-1,-1), 6),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                        ('LEFTPADDING', (0,0), (-1,-1), 8),
                        ('RIGHTPADDING', (0,0), (-1,-1), 8),
                    ]))
                    story.append(ev_table)
                    story.append(Spacer(1, 8))

                story.append(Spacer(1, 10))

        story.append(PageBreak())

        # =========================================================================
        # FINAL PAGES — SOURCES OVERVIEW (RPi_CSR Exact Layout)
        # =========================================================================
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
        story.append(Spacer(1, 12))
        story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#e2e8f0"), spaceBefore=2, spaceAfter=12))

        story.append(Paragraph("<b>TOP SOURCES</b>", self.styles['SectionHeading']))
        story.append(Paragraph(
            "The sources with the highest number of matches within the submission. Overlapping sources will not be displayed.",
            self.styles['SubDetailText']
        ))
        story.append(Spacer(1, 10))

        if not top_sources:
            story.append(Paragraph(
                "<i>No external sources exceeded the similarity threshold.</i>",
                self.styles['SubDetailText']
            ))
        else:
            # Table of sources matching RPi_CSR style
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

            src_table = Table(src_rows, colWidths=[35, 435, 62])
            src_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('ALIGN', (2,0), (2,-1), 'RIGHT'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 8),
                ('TOPPADDING', (0,0), (-1,-1), 8),
                ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor("#f1f5f9")),
            ]))
            story.append(src_table)

        story.append(Spacer(1, 16))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0"), spaceBefore=4, spaceAfter=10))

        # Methodology, Exclusions & Legal Disclaimer
        story.append(Paragraph("<b>METHODOLOGY & DISCLAIMER</b>", self.styles['MetaLabel']))
        story.append(Spacer(1, 4))
        story.append(Paragraph(
            f"<b>Calculation Method:</b> {summary.calculation_method}.<br/>"
            f"<b>Exclusions Applied:</b> Bibliographic references, quotation blocks, standard academic phrasing, and duplicate source occurrences.<br/>"
            f"<b>Legal & Academic Disclaimer:</b> {summary.disclaimer}",
            self.styles['SubDetailText']
        ))

        # Build Document using NumberedCanvas
        doc.build(story, canvasmaker=NumberedCanvas)
        return self.output_path
