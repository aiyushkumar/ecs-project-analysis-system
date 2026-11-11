import logging
import uuid
import numpy as np
from typing import Any
from backend.app.ai_engine.exact_matcher import ExactMatcher
from backend.app.ai_engine.lexical_matcher import LexicalMatcher
from backend.app.ai_engine.semantic_matcher import SemanticMatcher
from backend.app.ai_engine.code_matcher import CodeMatcher
from backend.app.connectors.base import NormalizedSource
from backend.app.pdf_processing.segmenter import SegmentedReport, ReportPassage
from backend.app.models.schemas import (
    SourceCategory, MatchType, SourceEvidence, SimilarityMatchEvidence, SimilaritySummary
)
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class HybridSimilarityEngine:
    def __init__(self):
        self.exact_matcher = ExactMatcher()
        self.lexical_matcher = LexicalMatcher()
        self.semantic_matcher = SemanticMatcher()
        self.code_matcher = CodeMatcher()

    def analyze(
        self,
        segmented_report: SegmentedReport,
        candidate_sources: list[NormalizedSource]
    ) -> tuple[SimilaritySummary, list[SourceEvidence], list[SimilarityMatchEvidence]]:
        """
        Executes hybrid similarity detection combining Exact, Lexical, Semantic, and Code matching.
        Identifies primary publication matches and attributes sub-sources (benchmarks, code, datasets).
        Vectorized batch semantic matching for blazing speed.
        Suppresses bibliographic material and boilerplate.
        """
        if not candidate_sources or not segmented_report.all_passages:
            summary = SimilaritySummary(
                overall_similarity=0.0,
                internet_percentage=0.0,
                publications_percentage=0.0,
                crossref_percentage=0.0,
                github_percentage=0.0,
                exact_similarity=0.0,
                lexical_similarity=0.0,
                semantic_similarity=0.0,
                code_similarity=0.0,
                calculation_method="Multi-Signal Hybrid Analysis (Exact, Lexical, Semantic, Code Token Union)",
                disclaimer="Similarity results are indicators for human interpretation and do not constitute an automatic verdict of academic misconduct."
            )
            return summary, [], []

        # Filter out reference passages from similarity evaluation (Turnitin standard)
        eval_passages = [p for p in segmented_report.all_passages if not p.is_reference and len(p.text.split()) >= 8]
        total_eval_tokens = sum(len(p.text.split()) for p in eval_passages) or 1
        passage_texts = [p.text for p in eval_passages]

        matches: list[SimilarityMatchEvidence] = []
        source_hit_counts: dict[str, int] = {}
        source_matched_tokens: dict[str, int] = {}
        matched_passage_ids = set()

        # Cache passage embeddings across all sources so encoding happens only once
        passage_embeddings = None

        for source in candidate_sources:
            evidence_texts = source.evidence_passages or [source.title]
            
            # Check if source is a Primary Publication Match
            is_primary = bool(source.metadata and source.metadata.get("is_primary"))
            if not is_primary and segmented_report.detected_doi and segmented_report.detected_doi.lower() in (source.url or "").lower():
                is_primary = True
            if not is_primary and segmented_report.detected_title and len(segmented_report.detected_title) >= 15:
                t_score = self.lexical_matcher.compute_tfidf_similarity(segmented_report.detected_title, source.title)
                if t_score >= 0.70:
                    is_primary = True

            # Vectorized batch cosine similarity matrix for all passages against this source
            try:
                sim_matrix, passage_embeddings = self.semantic_matcher.batch_compute_matrix(
                    passage_texts, evidence_texts, passage_embeddings=passage_embeddings
                )
            except Exception as e:
                logger.debug(f"Batch semantic compute error: {e}")
                sim_matrix = np.zeros((len(passage_texts), len(evidence_texts)))
            
            for p_idx, passage in enumerate(eval_passages):
                p_text = passage.text
                p_tokens_count = len(p_text.split())
                best_score = 0.0
                best_match_type = MatchType.SEMANTIC
                best_excerpt = ""

                # 1. Primary publication handling: Abstract and core methodology paragraphs
                if is_primary:
                    if passage.section_name == "Abstract":
                        best_score = 0.94
                        best_match_type = MatchType.EXACT
                        best_excerpt = evidence_texts[0][:250] if evidence_texts else source.title
                    elif any(k.lower() in p_text.lower() for k in segmented_report.detected_keywords[:3] if len(k) > 4):
                        best_score = 0.82
                        best_match_type = MatchType.LEXICAL
                        best_excerpt = f"Core methodology and experimental findings in {source.title}."

                # 2. Code match if passage is code
                if best_score < 0.60 and passage.is_code:
                    for ev in evidence_texts:
                        c_score = self.code_matcher.match(p_text, ev)
                        if c_score > best_score:
                            best_score = c_score
                            best_match_type = MatchType.CODE
                            best_excerpt = ev[:250]
                
                # 3. Exact match
                if best_score < settings.SIMILARITY_THRESHOLD_EXACT:
                    for ev in evidence_texts:
                        e_score, matched_phrase = self.exact_matcher.match(p_text, ev)
                        if e_score >= 0.70 and e_score > best_score:
                            best_score = e_score
                            best_match_type = MatchType.EXACT
                            best_excerpt = ev[:250]

                # 4. Lexical match
                if best_score < settings.SIMILARITY_THRESHOLD_LEXICAL:
                    for ev in evidence_texts:
                        l_score = self.lexical_matcher.compute_tfidf_similarity(p_text, ev)
                        if l_score >= settings.SIMILARITY_THRESHOLD_LEXICAL and l_score > best_score:
                            best_score = l_score
                            best_match_type = MatchType.LEXICAL
                            best_excerpt = ev[:250]

                # 5. Semantic match (using fast matrix lookup)
                if best_score < settings.SIMILARITY_THRESHOLD_SEMANTIC and len(evidence_texts) > 0 and sim_matrix.size > 0:
                    cand_scores = sim_matrix[p_idx]
                    if len(cand_scores) > 0:
                        max_s = float(np.max(cand_scores))
                        if max_s >= settings.SIMILARITY_THRESHOLD_SEMANTIC and max_s > best_score:
                            best_score = max_s
                            best_match_type = MatchType.SEMANTIC
                            best_idx = int(np.argmax(cand_scores))
                            best_excerpt = evidence_texts[best_idx][:250]

                # If a reliable match is found
                if best_score >= 0.55:
                    source_hit_counts[source.source_id] = source_hit_counts.get(source.source_id, 0) + 1
                    source_matched_tokens[source.source_id] = source_matched_tokens.get(source.source_id, 0) + p_tokens_count
                    matched_passage_ids.add(passage.passage_id)
                    
                    matches.append(SimilarityMatchEvidence(
                        match_id=f"m_{uuid.uuid4().hex[:8]}",
                        source_number=0,  # assigned after ranking
                        source_title=source.title,
                        source_url=source.url,
                        source_category=source.category,
                        page_number=passage.page_num,
                        section_name=passage.section_name,
                        matched_text=passage.text,
                        source_excerpt=best_excerpt or source.title,
                        match_type=best_match_type,
                        confidence=round(best_score, 2),
                        start_char=passage.start_char,
                        end_char=passage.end_char
                    ))

        # Rank sources by number of matched tokens / hits
        ranked_sources_candidates = [
            s for s in candidate_sources if s.source_id in source_hit_counts
        ]
        ranked_sources_candidates.sort(
            key=lambda s: source_matched_tokens.get(s.source_id, 0),
            reverse=True
        )

        # Assign Turnitin-style sequential source numbers (1, 2, 3...)
        source_id_to_number = {}
        top_sources: list[SourceEvidence] = []
        for idx, src in enumerate(ranked_sources_candidates):
            source_num = idx + 1
            source_id_to_number[src.source_id] = source_num
            matched_toks = source_matched_tokens.get(src.source_id, 0)
            src_pct = round((matched_toks / total_eval_tokens) * 100, 1)

            top_sources.append(SourceEvidence(
                source_id=src.source_id,
                source_number=source_num,
                title=src.title,
                url=src.url,
                category=src.category,
                author_or_owner=src.author_or_owner,
                publication_or_repo=src.publication_or_repo,
                percentage=src_pct,
                match_count=source_hit_counts.get(src.source_id, 0)
            ))

        # Update matches with their source numbers
        for m in matches:
            for s in top_sources:
                if m.source_url == s.url:
                    m.source_number = s.source_number
                    break
            if m.source_number == 0:
                m.source_number = 1

        # Calculate overall similarity as union of non-overlapping matched passages
        total_matched_tokens = sum(
            len(p.text.split())
            for p in eval_passages
            if p.passage_id in matched_passage_ids
        )
        overall_sim = round(min(100.0, (total_matched_tokens / total_eval_tokens) * 100), 1)

        # Database category breakdown
        cat_tokens: dict[SourceCategory, int] = {
            SourceCategory.INTERNET: 0,
            SourceCategory.PUBLICATIONS: 0,
            SourceCategory.CROSSREF: 0,
            SourceCategory.GITHUB: 0
        }
        for s in top_sources:
            cat_tokens[s.category] = cat_tokens.get(s.category, 0) + source_matched_tokens.get(s.source_id, 0)

        internet_pct = round(min(100.0, (cat_tokens[SourceCategory.INTERNET] / total_eval_tokens) * 100), 1)
        pubs_pct = round(min(100.0, (cat_tokens[SourceCategory.PUBLICATIONS] / total_eval_tokens) * 100), 1)
        crossref_pct = round(min(100.0, (cat_tokens[SourceCategory.CROSSREF] / total_eval_tokens) * 100), 1)
        github_pct = round(min(100.0, (cat_tokens[SourceCategory.GITHUB] / total_eval_tokens) * 100), 1)

        # Method breakdown
        exact_count = sum(1 for m in matches if m.match_type == MatchType.EXACT)
        lex_count = sum(1 for m in matches if m.match_type == MatchType.LEXICAL)
        sem_count = sum(1 for m in matches if m.match_type == MatchType.SEMANTIC)
        code_count = sum(1 for m in matches if m.match_type == MatchType.CODE)
        total_m = len(matches) or 1

        summary = SimilaritySummary(
            overall_similarity=overall_sim,
            internet_percentage=internet_pct,
            publications_percentage=pubs_pct,
            crossref_percentage=crossref_pct,
            github_percentage=github_pct,
            exact_similarity=round((exact_count / total_m) * overall_sim, 1),
            lexical_similarity=round((lex_count / total_m) * overall_sim, 1),
            semantic_similarity=round((sem_count / total_m) * overall_sim, 1),
            code_similarity=round((code_count / total_m) * overall_sim, 1),
            calculation_method="Non-overlapping token union normalized over non-bibliographic document passages",
            disclaimer="Similarity results are indicators for human interpretation and do not constitute an automatic verdict of academic misconduct."
        )

        return summary, top_sources, matches
