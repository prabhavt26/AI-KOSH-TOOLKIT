from fastapi import APIRouter, Request, Depends
from sqlalchemy import text
import redis
from datetime import datetime, timezone

from app.database import get_async_db
from app.config import settings
from app.storage.s3_client import s3_client
from app.worker.celery_app import celery_app

router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
async def get_health(request: Request, db=Depends(get_async_db)):
    """Returns the dependency connectivity check result."""
    deps = {"postgres": "error", "redis": "error", "s3": "error", "celery_workers": "error"}
    
    # 1. Postgres
    try:
        await db.execute(text("SELECT 1"))
        deps["postgres"] = "ok"
    except Exception:
        pass
        
    # 2. Redis
    try:
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)
        if r.ping():
            deps["redis"] = "ok"
    except Exception:
        pass
        
    # 3. S3
    try:
        if s3_client.s3:
            s3_client.s3.list_buckets()
            deps["s3"] = "ok"
    except Exception:
        pass
        
    # 4. Celery Workers
    try:
        insp = celery_app.control.inspect(timeout=1.0)
        active_workers = insp.ping() if insp else None
        if active_workers:
            deps["celery_workers"] = "ok"
        else:
            deps["celery_workers"] = "no_workers"
    except Exception:
        deps["celery_workers"] = "error"
        
    overall_status = "healthy" if all(v == "ok" for v in deps.values()) else ("degraded" if any(v == "ok" for v in deps.values()) else "unhealthy")
    
    # Security gating: internal requests or explicitly requested details
    is_internal = request.headers.get("X-Internal-Request") == "true" or settings.ENVIRONMENT != "production"
    
    resp = {
        "status": overall_status,
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc)
    }
    if is_internal:
        resp["dependencies"] = deps
        
    return resp
