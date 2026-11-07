import logging
import threading
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

_shared_model = None
_model_lock = threading.Lock()
_model_failed = False

def get_shared_model():
    global _shared_model, _model_failed
    if _model_failed:
        return None
    if _shared_model is None:
        with _model_lock:
            if _shared_model is None:
                try:
                    from sentence_transformers import SentenceTransformer
                    _shared_model = SentenceTransformer("all-MiniLM-L6-v2")
                    logger.info("SentenceTransformer 'all-MiniLM-L6-v2' loaded into shared memory.")
                except Exception as e:
                    logger.warning(f"SentenceTransformer fallback active: {e}")
                    _model_failed = True
                    _shared_model = None
    return _shared_model

class SemanticMatcher:
    """
    Computes semantic similarity using Sentence Transformers or dense text embeddings.
    Reuses a cached in-memory singleton model for ultra-high throughput batch performance.
    """
    def __init__(self):
        self.model = get_shared_model()

    def encode(self, texts: list[str]) -> np.ndarray:
        """Encodes list of strings into embedding vectors."""
        model = self.model or get_shared_model()
        if model is not None:
            try:
                return model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            except Exception as e:
                logger.debug(f"Embedding encoding issue: {e}")
        
        # Fallback dense TF-IDF vectorizer if neural model is loading or unavailable
        from sklearn.feature_extraction.text import TfidfVectorizer
        vec = TfidfVectorizer(max_features=384, stop_words='english')
        try:
            return vec.fit_transform(texts).toarray()
        except Exception:
            return np.zeros((len(texts), 384))

    def compute_similarity(self, passage: str, candidate_texts: list[str]) -> list[float]:
        """
        Computes cosine similarity between query passage and multiple candidate texts.
        """
        if not candidate_texts:
            return []
        
        all_texts = [passage] + candidate_texts
        embeddings = self.encode(all_texts)
        
        query_vec = embeddings[0:1]
        cand_vecs = embeddings[1:]
        
        sims = cosine_similarity(query_vec, cand_vecs)[0]
        return [float(max(0.0, s)) for s in sims]
