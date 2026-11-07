import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Resolve base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
WORKSPACE_DIR = BASE_DIR.parent
STORAGE_BASE = WORKSPACE_DIR / "storage"

class Settings(BaseSettings):
    APP_NAME: str = "ECS — PROJECT ANALYSIS SYSTEM"
    APP_TAGLINE: str = "Intelligent Project Similarity Analysis. Transparent. Evidence-Based."
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Storage settings
    STORAGE_DIR: Path = STORAGE_BASE
    UPLOAD_DIR: Path = STORAGE_BASE / "uploads"
    REPORT_DIR: Path = STORAGE_BASE / "reports"
    TEMP_DIR: Path = STORAGE_BASE / "temp"
    
    # Limits and validation
    MAX_FILE_SIZE_MB: int = 50
    MAX_PAGE_LIMIT: int = 300
    MAX_BATCH_SIZE: int = 500  # Supports > 300 reports
    ALLOWED_EXTENSIONS: list[str] = [".pdf", ".zip"]
    
    # Privacy and security
    PRIVATE_TOKEN_LENGTH: int = 32
    RETENTION_HOURS: int = 48
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # AI Engine & NLP
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    DEVICE: str = "cpu"
    SIMILARITY_THRESHOLD_EXACT: float = 0.85
    SIMILARITY_THRESHOLD_LEXICAL: float = 0.55
    SIMILARITY_THRESHOLD_SEMANTIC: float = 0.65
    SIMILARITY_THRESHOLD_CODE: float = 0.70
    
    # Queue / Celery
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    USE_IN_MEMORY_QUEUE: bool = True  # Automatically falls back to async background worker if Redis is offline
    CONCURRENT_WORKERS: int = 16
    
    # External APIs (Optional, zero cost / free tier)
    GITHUB_TOKEN: str | None = os.getenv("GITHUB_TOKEN", None)
    SEARXNG_URL: str | None = os.getenv("SEARXNG_URL", None)
    CROSSREF_MAILTO: str = os.getenv("CROSSREF_MAILTO", "ecs-project@analysis.org")
    
    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()

# Ensure directories exist
for p in [settings.STORAGE_DIR, settings.UPLOAD_DIR, settings.REPORT_DIR, settings.TEMP_DIR]:
    p.mkdir(parents=True, exist_ok=True)
