import re
from difflib import SequenceMatcher

KEYWORDS = {
    "def", "class", "return", "import", "from", "for", "while", "if", "else", "elif",
    "try", "except", "finally", "with", "as", "lambda", "yield", "async", "await",
    "public", "private", "protected", "static", "void", "int", "float", "double", "char",
    "struct", "namespace", "include", "template", "typename", "const", "let", "var", "function"
}

class CodeMatcher:
    """
    Computes programming code similarity by stripping comments/whitespace,
    normalizing variable names, and performing token-level n-gram and sequence comparison.
    """
    def normalize_code(self, code_str: str) -> list[str]:
        # Remove single-line comments (# or //)
        code = re.sub(r'(#|//).*$', '', code_str, flags=re.MULTILINE)
        # Remove multi-line comments (/* ... */ or ''' ... ''')
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        code = re.sub(r"'''.*?'''", '', code, flags=re.DOTALL)
        code = re.sub(r'""".*?"""', '', code, flags=re.DOTALL)
        
        # Tokenize code into keywords, operators, brackets, and generic identifiers
        raw_tokens = re.findall(r'[a-zA-Z_]\w*|[0-9]+|[^\s\w]', code)
        normalized = []
        for t in raw_tokens:
            if t in KEYWORDS:
                normalized.append(t)
            elif re.match(r'^[a-zA-Z_]\w*$', t):
                normalized.append("ID")  # normalize variable/function names
            elif re.match(r'^[0-9]+$', t):
                normalized.append("NUM")
            else:
                normalized.append(t)
        return normalized

    def match(self, report_code: str, source_code: str) -> float:
        r_tokens = self.normalize_code(report_code)
        s_tokens = self.normalize_code(source_code)
        
        if len(r_tokens) < 10 or len(s_tokens) < 10:
            return 0.0
            
        matcher = SequenceMatcher(None, r_tokens, s_tokens)
        match = matcher.find_longest_match(0, len(r_tokens), 0, len(s_tokens))
        
        # If matching token sequence is at least 12 tokens
        if match.size >= 12:
            return float(min(1.0, match.size / len(r_tokens)))
            
        ratio = matcher.ratio()
        return float(ratio) if ratio > 0.65 else 0.0
