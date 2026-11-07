import pytest
from backend.app.ai_engine.exact_matcher import ExactMatcher
from backend.app.ai_engine.lexical_matcher import LexicalMatcher
from backend.app.ai_engine.semantic_matcher import SemanticMatcher
from backend.app.ai_engine.code_matcher import CodeMatcher
from backend.app.ai_engine.hybrid_engine import HybridSimilarityEngine
from backend.app.connectors.base import NormalizedSource
from backend.app.models.schemas import SourceCategory
from backend.app.pdf_processing.segmenter import SegmentedReport, ReportPassage

def test_exact_matcher():
    matcher = ExactMatcher()
    p1 = "The Raspberry Pi is a small but versatile prototyping device that has revolutionized scientific research."
    p2 = "Indeed, the Raspberry Pi is a small but versatile prototyping device that has revolutionized scientific research and robotics."
    
    score, phrase = matcher.match(p1, p2)
    assert score >= 0.70
    assert phrase is not None

    # Boilerplate suppression test
    boilerplate = "Submitted in partial fulfillment of the requirements for the award of Bachelor of Technology"
    b_score, _ = matcher.match(boilerplate, boilerplate)
    assert b_score == 0.0

def test_lexical_matcher():
    matcher = LexicalMatcher()
    t1 = "Convolutional neural network model for automated crop pest detection in smart agriculture systems."
    t2 = "Deep learning convolutional neural network applied to agricultural crop pest detection and monitoring."
    
    score = matcher.compute_tfidf_similarity(t1, t2)
    assert score > 0.30

def test_code_matcher():
    matcher = CodeMatcher()
    c1 = """
    def train_model(X, y):
        model = LogisticRegression()
        model.fit(X, y)
        return model
    """
    c2 = """
    def train_classifier(features, labels):
        clf = LogisticRegression()
        clf.fit(features, labels)
        return clf
    """
    score = matcher.match(c1, c2)
    assert score > 0.60

def test_hybrid_engine():
    engine = HybridSimilarityEngine()
    rep = SegmentedReport()
    rep.all_passages = [
        ReportPassage(
            passage_id="p1",
            text="The Raspberry Pi is a small but versatile single board prototyping computer widely used in robotics.",
            page_num=1,
            section_name="Introduction"
        )
    ]
    
    source = NormalizedSource(
        source_id="src1",
        title="Raspberry Pi Prototyping Review",
        category=SourceCategory.PUBLICATIONS,
        url="https://doi.org/10.1109/test",
        evidence_passages=["The Raspberry Pi is a small but versatile single board prototyping computer widely used in robotics."]
    )

    summary, top_sources, matches = engine.analyze(rep, [source])
    assert summary.overall_similarity > 0.0
    assert len(top_sources) == 1
    assert top_sources[0].source_number == 1
    assert len(matches) == 1
    assert matches[0].source_number == 1
