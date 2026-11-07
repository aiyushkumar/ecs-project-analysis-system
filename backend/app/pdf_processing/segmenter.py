import re
from typing import NamedTuple
from backend.app.pdf_processing.extractor import ExtractedDocument, ExtractedBlock

SECTION_PATTERNS = [
    ("Abstract", re.compile(r'^\s*(?:[0-9]+\.?\s*)?abstract\b', re.IGNORECASE)),
    ("Introduction", re.compile(r'^\s*(?:[0-9]+\.?\s*)?introduction\b', re.IGNORECASE)),
    ("Problem Statement", re.compile(r'^\s*(?:[0-9]+\.?\s*)?problem\s+statement\b', re.IGNORECASE)),
    ("Literature Survey", re.compile(r'^\s*(?:[0-9]+\.?\s*)?(?:literature\s+(?:survey|review)|related\s+works?)\b', re.IGNORECASE)),
    ("Proposed Methodology", re.compile(r'^\s*(?:[0-9]+\.?\s*)?(?:proposed\s+(?:methodology|system|work|model)|methodology)\b', re.IGNORECASE)),
    ("System Architecture", re.compile(r'^\s*(?:[0-9]+\.?\s*)?(?:system\s+architecture|architecture|workflow)\b', re.IGNORECASE)),
    ("Implementation", re.compile(r'^\s*(?:[0-9]+\.?\s*)?(?:implementation|system\s+design|experimental\s+setup)\b', re.IGNORECASE)),
    ("Results & Discussion", re.compile(r'^\s*(?:[0-9]+\.?\s*)?(?:results?(?:\s+and\s+discussion)?|evaluation|performance\s+analysis)\b', re.IGNORECASE)),
    ("Conclusion", re.compile(r'^\s*(?:[0-9]+\.?\s*)?(?:conclusion(?:\s+and\s+future\s+scope)?|summary)\b', re.IGNORECASE)),
    ("References", re.compile(r'^\s*(?:[0-9]+\.?\s*)?(?:references|bibliography)\b', re.IGNORECASE)),
]

class ReportPassage:
    def __init__(
        self,
        passage_id: str,
        text: str,
        page_num: int,
        section_name: str,
        bbox: tuple[float, float, float, float] = (0, 0, 0, 0),
        is_code: bool = False,
        is_reference: bool = False,
        start_char: int = 0,
        end_char: int = 0
    ):
        self.passage_id = passage_id
        self.text = text.strip()
        self.page_num = page_num
        self.section_name = section_name
        self.bbox = bbox
        self.is_code = is_code
        self.is_reference = is_reference
        self.start_char = start_char
        self.end_char = end_char

class SegmentedReport:
    def __init__(self):
        self.sections: dict[str, list[ReportPassage]] = {}
        self.detected_section_names: list[str] = []
        self.all_passages: list[ReportPassage] = []
        self.references: list[str] = []

def segment_report(doc: ExtractedDocument) -> SegmentedReport:
    """
    Identifies academic headings across pages, segments blocks into logical sections,
    and breaks text into sliding passages of ~50-100 words with page & section metadata.
    """
    result = SegmentedReport()
    current_section = "Introduction"
    in_references = False
    
    passage_counter = 0

    for block in doc.blocks:
        text = block.text.strip()
        if not text:
            continue
        
        # Check if block is a new section heading
        first_line = text.split("\n")[0].strip()
        matched_section = None
        for sec_name, pattern in SECTION_PATTERNS:
            if pattern.search(first_line):
                matched_section = sec_name
                break
        
        if matched_section:
            current_section = matched_section
            if current_section not in result.detected_section_names:
                result.detected_section_names.append(current_section)
            if current_section == "References":
                in_references = True
        
        # If we are in references, collect bibliography
        if in_references:
            result.references.append(text)
        
        # Split block into manageable sentences/passages for fine-grained matching
        # Avoid splitting code blocks
        if block.is_code:
            passage_counter += 1
            p = ReportPassage(
                passage_id=f"p_{passage_counter}",
                text=text,
                page_num=block.page_num,
                section_name=current_section,
                bbox=block.bbox,
                is_code=True,
                is_reference=in_references
            )
            result.all_passages.append(p)
            result.sections.setdefault(current_section, []).append(p)
        else:
            # Sentence-level or multi-sentence passage chunks
            # Split by period/newline but group into ~40-80 words
            sentences = re.split(r'(?<=[.!?])\s+', text)
            current_chunk = []
            current_word_count = 0
            
            for s in sentences:
                s_clean = s.strip()
                if not s_clean:
                    continue
                words = s_clean.split()
                current_chunk.append(s_clean)
                current_word_count += len(words)
                
                if current_word_count >= 35:
                    chunk_text = " ".join(current_chunk)
                    passage_counter += 1
                    p = ReportPassage(
                        passage_id=f"p_{passage_counter}",
                        text=chunk_text,
                        page_num=block.page_num,
                        section_name=current_section,
                        bbox=block.bbox,
                        is_code=False,
                        is_reference=in_references
                    )
                    result.all_passages.append(p)
                    result.sections.setdefault(current_section, []).append(p)
                    current_chunk = []
                    current_word_count = 0
            
            if current_chunk:
                chunk_text = " ".join(current_chunk)
                if len(chunk_text.split()) >= 8:  # ignore tiny trailing fragments
                    passage_counter += 1
                    p = ReportPassage(
                        passage_id=f"p_{passage_counter}",
                        text=chunk_text,
                        page_num=block.page_num,
                        section_name=current_section,
                        bbox=block.bbox,
                        is_code=False,
                        is_reference=in_references
                    )
                    result.all_passages.append(p)
                    result.sections.setdefault(current_section, []).append(p)

    # Fallback if no sections were identified
    if not result.detected_section_names:
        result.detected_section_names = ["General Body"]
        
    return result
