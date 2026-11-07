from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

class ProcessingStage(str, Enum):
    QUEUED = "Queued for Processing"
    UPLOAD_VALIDATION = "Upload Validation"
    PDF_TEXT_EXTRACTION = "PDF Text Extraction"
    DOCUMENT_UNDERSTANDING = "Document Understanding"
    GITHUB_SOURCE_DISCOVERY = "GitHub Source Discovery"
    RESEARCH_PAPER_ANALYSIS = "Research Paper Analysis"
    INTERNET_SOURCE_ANALYSIS = "Internet Source Analysis"
    SIMILARITY_DETECTION = "Similarity Detection"
    PDF_REPORT_GENERATION = "PDF Report Generation"
    COMPLETED = "Analysis Completed"
    FAILED = "Analysis Failed"

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class SourceCategory(str, Enum):
    INTERNET = "Internet database"
    PUBLICATIONS = "Publications database"
    CROSSREF = "Crossref database"
    GITHUB = "Submitted Works / GitHub"

class MatchType(str, Enum):
    EXACT = "Exact Text Matching"
    LEXICAL = "Lexical Similarity"
    SEMANTIC = "Semantic Similarity"
    CODE = "Code Similarity"

class SourceEvidence(BaseModel):
    source_id: str
    source_number: int
    title: str
    url: str
    category: SourceCategory
    author_or_owner: str = "Unknown"
    publication_or_repo: str = ""
    percentage: float = 0.0
    match_count: int = 0
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)

class SimilarityMatchEvidence(BaseModel):
    match_id: str
    source_number: int
    source_title: str
    source_url: str
    source_category: SourceCategory
    page_number: int
    section_name: str
    matched_text: str
    source_excerpt: str
    match_type: MatchType
    confidence: float
    start_char: int = 0
    end_char: int = 0

class AnalysisJobCreateResponse(BaseModel):
    job_id: str
    original_filename: str
    status: JobStatus
    stage: ProcessingStage
    private_token: str
    status_url: str
    result_url: str
    created_at: datetime

class BatchJobCreateResponse(BaseModel):
    batch_id: str
    total_files: int
    jobs: list[AnalysisJobCreateResponse]
    private_token: str
    status_url: str
    download_url: str
    created_at: datetime

class AnalysisJobStatusResponse(BaseModel):
    job_id: str
    batch_id: str | None = None
    original_filename: str
    file_size_bytes: int
    page_count: int
    word_count: int
    character_count: int
    status: JobStatus
    stage: ProcessingStage
    stage_progress: int = 0  # 0 to 100%
    overall_similarity: float = 0.0
    error_message: str | None = None
    processing_duration_sec: float | None = None
    download_available: bool = False
    download_url: str | None = None
    created_at: datetime
    updated_at: datetime

class BatchStatusResponse(BaseModel):
    batch_id: str
    total_files: int
    completed_files: int
    failed_files: int
    processing_files: int
    status: JobStatus
    progress_percentage: float
    jobs: list[AnalysisJobStatusResponse]
    zip_download_available: bool = False
    zip_download_url: str | None = None
    created_at: datetime
    updated_at: datetime

class SimilaritySummary(BaseModel):
    overall_similarity: float
    internet_percentage: float
    publications_percentage: float
    crossref_percentage: float
    github_percentage: float
    exact_similarity: float
    lexical_similarity: float
    semantic_similarity: float
    code_similarity: float
    calculation_method: str
    disclaimer: str

class AnalysisResultResponse(BaseModel):
    job_id: str
    original_filename: str
    report_id: str
    word_count: int
    character_count: int
    page_count: int
    file_size_mb: float
    submission_date: str
    report_date: str
    processing_duration_seconds: float
    similarity_summary: SimilaritySummary
    top_sources: list[SourceEvidence]
    matches: list[SimilarityMatchEvidence]
    sections_detected: list[str]
    download_url: str
