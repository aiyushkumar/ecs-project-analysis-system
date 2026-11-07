import os
from celery import Celery
from backend.app.core.config import settings

celery_app = Celery(
    "ecs_analysis_system",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=1800,  # 30 min max per large PDF
    worker_concurrency=settings.CONCURRENT_WORKERS,
    worker_prefetch_multiplier=1,
)
