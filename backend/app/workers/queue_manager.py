import concurrent.futures
import logging
from pathlib import Path
from backend.app.core.config import settings
from backend.app.core.database import DatabaseManager
from backend.app.workers.tasks import sync_run_pipeline, celery_process_pdf_job

logger = logging.getLogger(__name__)

class QueueManager:
    """
    Unified Queue Manager supporting both Celery + Redis for production
    and high-throughput concurrent thread execution for frictionless local running.
    """
    _executor = concurrent.futures.ThreadPoolExecutor(max_workers=settings.CONCURRENT_WORKERS)
    _celery_active = False

    @classmethod
    def check_celery(cls) -> bool:
        if not settings.USE_IN_MEMORY_QUEUE:
            try:
                import redis
                r = redis.from_url(settings.REDIS_URL, socket_timeout=1)
                r.ping()
                cls._celery_active = True
                return True
            except Exception:
                cls._celery_active = False
                return False
        return False

    @classmethod
    def enqueue_job(cls, job_id: str, file_path: Path):
        """Enqueue an independent analysis job into background queue."""
        DatabaseManager.update_job_stage(job_id, "Queued for Processing", stage_progress=0)

        if cls.check_celery() and celery_process_pdf_job is not None:
            try:
                celery_process_pdf_job.delay(job_id, str(file_path))
                logger.info(f"Dispatched job {job_id} to Celery queue.")
                return
            except Exception as e:
                logger.warning(f"Celery dispatch failed: {e}. Falling back to internal worker pool.")

        # Fallback to concurrent thread pool executor
        cls._executor.submit(sync_run_pipeline, job_id, str(file_path))
        logger.info(f"Submitted job {job_id} to concurrent worker pool.")

    @classmethod
    def retry_failed_jobs(cls, batch_id: str) -> int:
        """Retries all failed jobs in a given batch."""
        jobs = DatabaseManager.get_batch_jobs(batch_id)
        failed_jobs = [j for j in jobs if j.get("status") == "failed"]
        
        retried_count = 0
        for j in failed_jobs:
            job_id = j["id"]
            # Look up uploaded file
            file_candidates = list(settings.UPLOAD_DIR.glob(f"{job_id}_*"))
            if file_candidates:
                file_path = file_candidates[0]
                cls.enqueue_job(job_id, file_path)
                retried_count += 1

        return retried_count
