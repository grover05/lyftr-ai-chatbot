from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.config import settings
from app.schemas import HealthResponse
import litellm

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    """
    Returns HTTP 200 only when:
    - Application is running
    - Database is reachable
    - Key pool is loaded
    """
    # 1. Verify database reachable
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database unreachable: {str(e)}")

    # 2. Verify key pool
    configured_keys = len(settings.key_pool)
    if configured_keys < 1:
        raise HTTPException(status_code=500, detail="No API keys configured")

    # 3. Verify LiteLLM cache status
    cache_enabled = litellm.cache is not None

    return HealthResponse(
        status="ok",
        keys_configured=configured_keys,
        cache_enabled=cache_enabled
    )
