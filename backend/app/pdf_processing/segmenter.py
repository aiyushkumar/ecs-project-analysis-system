import re
from typing import NamedTuple
from backend.app.pdf_processing.extractor import ExtractedDocument, ExtractedBlock

SECTION_PATTERNS = [
    ("Abstract", re.compile(r'^\s*(?:[0-9]+\.?\s*)?(?:a\s*b\s*s\s*t\s*r\s*a\s*c\s*t|abstract|executive\s+summary|synopsis)\b', re.IGNORECASE)),
    ("Introduction", re.compile(r'^\s*(?:[0-9]+\.?\s*)?introduction\b', re.IGNORECASE)),
    ("Problem Statement", re.compile(r'^\s*(?:[0-9]+\.?\s*)?problem\s+statement\b', re.IGNORECASE)),
    ("Literature Survey", re.compile(r'^\s*(?:[0-9]+\.?\s*)?(?:literature\s+(?:survey|review)|related\s+works?|background|prior\s+art|prior\s+work)\b', re.IGNORECASE)),
    ("Proposed Methodology", re.compile(r'^\s*(?:[0-9]+\.?\s*)?(?:proposed\s+(?:methodology|system|work|model)|methodology|materials\s+and\s+methods|system\s+design|methods|experimental\s+setup)\b', re.IGNORECASE)),
    ("System Architecture", re.compile(r'^\s*(?:[0-9]+\.?\s*)?(?:system\s+architecture|architecture|workflow)\b', re.IGNORECASE)),
    ("Implementation", re.compile(r'^\s*(?:[0-9]+\.?\s*)?(?:implementation|system\s+design|tool\s+design|experimental\s+setup)\b', re.IGNORECASE)),
    ("Results & Discussion", re.compile(r'^\s*(?:[0-9]+\.?\s*)?(?:results?(?:\s+and\s+discussion)?|evaluation|performance\s+analysis|experimental\s+results)\b', re.IGNORECASE)),
    ("Conclusion", re.compile(r'^\s*(?:[0-9]+\.?\s*)?(?:conclusion(?:\s+and\s+future\s+scope)?|summary|concluding\s+remarks)\b', re.IGNORECASE)),
    ("References", re.compile(r'^\s*(?:[0-9]+\.?\s*)?(?:references|bibliography|literature\s+cited)\b', re.IGNORECASE)),
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
        self.detected_title: str = ""
        self.detected_doi: str = ""
        self.detected_keywords: list[str] = []
        self.detected_repos: list[str] = []
        self.detected_dataset_urls: list[str] = []
        self.detected_authors: list[str] = []

def extract_document_metadata(doc: ExtractedDocument) -> dict:
    """
    Extracts high-fidelity academic metadata from document text and Page 1 layout blocks:
    - Real paper or project report title (filtering publisher headers, affiliations, journal names)
    - DOIs (e.g. 10.1016/j.ecoinf.2025.103193)
    - Keywords list
    - GitHub, GitLab, and Bitly source repository URLs
    - External dataset download URLs
    """
    journal_markers = [
        "contents lists available", "journal homepage", "sciencedirect", "elsevier",
        "springer", "ieee", "article info", "issn", "doi.org", "http://", "https://",
        "wiley", "nature", "proceedings of"
    ]
    affil_markers = [
        "university", "department", "school of", "college", "institute", "faculty of",
        "e-mail address", "corresponding author", "received", "accepted", "available online"
    ]
    
    # 1. Find DOI in first page or whole document
    dois = re.findall(r'10\.\d{4,9}/[A-Za-z0-9_.-]+', doc.full_text)
    detected_doi = dois[0] if dois else ""

    # 2. Extract Title from Page 1 blocks
    title_candidates = []
    seen_journal_header = False
    
    for b in doc.blocks[:15]:
        if b.page_num != 1:
            break
        txt = b.text.strip()
        lines = [l.strip() for l in txt.split("\n") if l.strip()]
        if not lines:
            continue
            
        first_line = lines[0]
        lower_txt = txt.lower()
        
        if any(m in lower_txt for m in ["journal homepage", "sciencedirect", "contents lists available"]):
            seen_journal_header = True
            continue
            
        if any(m in lower_txt for m in ["article info", "keywords:", "a b s t r a c t"]):
            break
            
        if any(m in lower_txt for m in affil_markers):
            continue
            
        # Avoid author lines (often have superscripts a, b, c, or comma separated list of names)
        if re.search(r'\b[a-z]\s*,\s*[A-Z]', txt) or txt.count(",") >= 3:
            continue

        if len(first_line) >= 20 and not any(m in first_line.lower() for m in journal_markers):
            title_candidates.append((seen_journal_header, len(first_line), first_line, " ".join(lines)))

    title_candidates.sort(key=lambda c: (c[0], c[1]), reverse=True)
    detected_title = title_candidates[0][3] if title_candidates else ""

    # 3. Keywords
    kw_match = re.search(r'Keywords:\s*([\s\S]*?)(?:A\s*B\s*S\s*T\s*R\s*A\s*C\s*T|Abstract|\n\s*\n\s*[0-9])', doc.full_text, re.I)
    keywords = []
    if kw_match:
        for k in re.split(r'[\n,;•]+', kw_match.group(1)):
            k_clean = k.strip()
            if 3 <= len(k_clean) <= 60 and not any(m in k_clean.lower() for m in journal_markers):
                keywords.append(k_clean)

    # 4. Repos & URLs
    urls = re.findall(r'https?://[^\s<>"\'\)]+', doc.full_text)
    repos = [u.rstrip(".,;") for u in urls if any(h in u.lower() for h in ["github.com", "bit.ly", "gitlab.com"])]
    dataset_urls = [u.rstrip(".,;") for u in urls if any(h in u.lower() for h in ["gts.ai", "kaggle.com", "zenodo", "huggingface"])]

    return {
        "title": detected_title,
        "doi": detected_doi,
        "keywords": keywords,
        "repos": list(set(repos)),
        "dataset_urls": list(set(dataset_urls))
    }

def segment_report(doc: ExtractedDocument) -> SegmentedReport:
    """
    Identifies academic headings across pages, segments blocks into logical sections,
    and breaks text into sliding passages of ~50-100 words with page & section metadata.
    Also extracts document-level metadata (title, DOI, keywords, repos, datasets).
    """
    result = SegmentedReport()
    
    # Extract rich metadata
    meta = extract_document_metadata(doc)
    result.detected_title = meta.get("title", "")
    result.detected_doi = meta.get("doi", "")
    result.detected_keywords = meta.get("keywords", [])
    result.detected_repos = meta.get("repos", [])
    result.detected_dataset_urls = meta.get("dataset_urls", [])
    
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
