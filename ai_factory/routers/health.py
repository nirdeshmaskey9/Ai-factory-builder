from fastapi import APIRouter
from ai_factory.models import ErrorResponse

router = APIRouter(tags=["system"])


@router.get("/healthcheck", summary="Simple health probe")
def healthcheck():
    """
    Health check endpoint returning static JSON useful for liveness probes.
    """
    return {"status": "ok", "service": "ai-factory-router-core", "phase": 1}
