import re
from difflib import SequenceMatcher

COMMON_BOILERPLATE = {
    "all rights reserved",
    "the rest of this paper is organized as follows",
    "in this paper we present",
    "in this paper we propose",
    "table of contents",
    "submitted in partial fulfillment of the requirements",
    "bachelor of technology in computer science",
    "department of computer science and engineering",
    "academic year",
    "certificate of bonafide work",
    "sincerely thank our faculty guide",
    "keywords:",
    "index terms"
}

def normalize_text(text: str) -> str:
    """Normalize text by converting to lowercase and stripping punctuation/extra whitespace."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    return " ".join(text.split())

def generate_ngrams(tokens: list[str], n: int = 7) -> list[tuple[str, ...]]:
    """Generates contiguous n-grams from a token list."""
    if len(tokens) < n:
        return [tuple(tokens)] if tokens else []
    return [tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]

class ExactMatcher:
    """
    Finds verbatim n-gram matches and exact phrase duplications while
    suppressing known academic boilerplate.
    """
    def __init__(self, n: int = 7, min_match_chars: int = 40):
        self.n = n
        self.min_match_chars = min_match_chars

    def is_boilerplate(self, phrase: str) -> bool:
        norm = normalize_text(phrase)
        for bp in COMMON_BOILERPLATE:
            if bp in norm:
                return True
        return False

    def match(self, report_passage: str, source_passage: str) -> tuple[float, str | None]:
        """
        Calculates exact string similarity ratio and identifies longest matching verbatim substring.
        """
        if self.is_boilerplate(report_passage):
            return 0.0, None

        norm_report = normalize_text(report_passage)
        norm_source = normalize_text(source_passage)
        
        if not norm_report or not norm_source:
            return 0.0, None

        # Quick check for verbatim inclusion
        if norm_report in norm_source:
            if len(norm_report) >= self.min_match_chars:
                return 1.0, report_passage
        
        # SequenceMatcher for longest contiguous match
        matcher = SequenceMatcher(None, norm_report, norm_source)
        match = matcher.find_longest_match(0, len(norm_report), 0, len(norm_source))
        
        if match.size >= self.min_match_chars:
            ratio = match.size / max(len(norm_report), 1)
            matched_phrase = norm_report[match.a : match.a + match.size]
            return min(ratio, 1.0), matched_phrase
        
        # N-gram overlap
        report_tokens = norm_report.split()
        source_tokens = norm_source.split()
        
        if len(report_tokens) >= self.n and len(source_tokens) >= self.n:
            r_ngrams = set(generate_ngrams(report_tokens, self.n))
            s_ngrams = set(generate_ngrams(source_tokens, self.n))
            common = r_ngrams.intersection(s_ngrams)
            if common:
                score = len(common) / len(r_ngrams)
                return score, " ".join(next(iter(common)))

        return 0.0, None
