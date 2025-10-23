from __future__ import annotations

from fastapi import APIRouter
import os


router = APIRouter(prefix="/factory", tags=["Factory"])


@router.get("/info")
def factory_info():
    version = os.getenv("FACTORY_VERSION", "v1.5-full-webapp-support")
    templates = [
        "fastapi_basic",
        "cli_basic",
        "ml_basic",
        "fastapi_full_app",
    ]
    return {
        "name": "AI Factory",
        "version": version,
        "status": "online",
        "banner": "AI Factory v1.3-gpt4o-builder - Live Planner Active",
        "healthy": True,
        "templates": templates,
    }


@router.get("/health")
def factory_health():
    return {
        "db": "OK",
        "planner": "OK",
        "deployer": "OK",
        "evaluator": "Partial (some routes missing)",
        "summary": "Operational",
    }
