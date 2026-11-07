from fastapi import HTTPException, Query, Header, status
from backend.app.core.database import DatabaseManager
from backend.app.core.security import verify_token

def verify_job_access(job_id: str, token: str = Query(None), x_private_token: str = Header(None, alias="X-Private-Token")) -> dict:
    raw_token = token or x_private_token
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Private retrieval token is required to access analysis results."
        )
    
    job = DatabaseManager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found.")

    if not verify_token(raw_token, job["private_token_hash"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or expired private access token.")

    return job

def verify_batch_access(batch_id: str, token: str = Query(None), x_private_token: str = Header(None, alias="X-Private-Token")) -> dict:
    raw_token = token or x_private_token
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Private retrieval token is required to access batch results."
        )

    batch = DatabaseManager.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Batch {batch_id} not found.")

    if not verify_token(raw_token, batch["private_token_hash"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or expired private access token.")

    return batch
