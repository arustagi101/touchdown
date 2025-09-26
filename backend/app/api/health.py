from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from app.core.config import settings
import redis.asyncio as redis

router = APIRouter()

@router.get("/")
async def health_check():
    return {"status": "healthy", "service": "touchdown-api"}

@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    checks = {"api": True, "database": False, "redis": False}

    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        pass

    try:
        r = redis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.close()
        checks["redis"] = True
    except Exception:
        pass

    all_healthy = all(checks.values())
    return {
        "ready": all_healthy,
        "checks": checks
    }