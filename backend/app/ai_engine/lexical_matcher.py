import math
import re
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rank_bm25 import BM25Okapi

def stem_token(word: str) -> str:
    """Lightweight rule-based suffix stemmer to match morphological variants."""
    w = word.lower()
    for suffix in ("ational", "tional", "isation", "ization", "ness", "ment", "ing", "tion", "sion", "able", "ible", "ies", "ied", "ed", "al", "ly", "es", "s"):
        if w.endswith(suffix) and len(w) > len(suffix) + 3:
            return w[:-len(suffix)]
    return w

class LexicalMatcher:
    """
    Computes lexical similarity using stemmed TF-IDF cosine similarity and BM25 candidate scoring.
    """
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            stop_words='english',
            max_features=5000
        )

    def tokenize(self, text: str) -> list[str]:
        raw_words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        return [stem_token(w) for w in raw_words]

    def compute_tfidf_similarity(self, passage: str, source_text: str) -> float:
        """Computes TF-IDF cosine similarity between two text snippets."""
        tokens1 = self.tokenize(passage)
        tokens2 = self.tokenize(source_text)
        
        if not tokens1 or not tokens2:
            return 0.0
        
        # Word overlap coefficient
        s1, s2 = set(tokens1), set(tokens2)
        overlap = len(s1.intersection(s2))
        jaccard = overlap / len(s1.union(s2)) if s1.union(s2) else 0.0

        try:
            tfidf = self.vectorizer.fit_transform([" ".join(tokens1), " ".join(tokens2)])
            sim = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
            # Blend TF-IDF with jaccard overlap for robust lexical scoring
            return float(max(sim, jaccard))
        except Exception:
            return float(jaccard)

    def compute_bm25_score(self, passage: str, corpus: list[str]) -> list[float]:
        """Scores a passage against a corpus of candidate texts using BM25."""
        tokenized_corpus = [self.tokenize(doc) for doc in corpus]
        tokenized_corpus = [doc if doc else ["empty"] for doc in tokenized_corpus]
        
        tokenized_query = self.tokenize(passage)
        if not tokenized_query or not tokenized_corpus:
            return [0.0] * len(corpus)
            
        bm25 = BM25Okapi(tokenized_corpus)
        scores = bm25.get_scores(tokenized_query)
        max_score = max(scores) if len(scores) > 0 and max(scores) > 0 else 1.0
        return [float(s / max_score) for s in scores]
