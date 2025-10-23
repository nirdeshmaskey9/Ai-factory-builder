from __future__ import annotations

from fastapi import APIRouter
import os


router = APIRouter(prefix="/factory", tags=["Factory"])


@router.get("/info")
def factory_info():
    version = os.getenv("FACTORY_VERSION", "v1.6.1-pre-phase2")
    templates = [
        # Core banks
        "fastapi_full_app",
        "fastapi_dashboard",
        "flask_minimal",
        "streamlit_basic",
        "automation_cli",
        "imagegen_fastapi",
        # Legacy identifiers
        "fastapi_basic",
        "cli_basic",
        "ml_basic",
    ]
    return {
        "name": "AI Factory",
        "version": version,
        "release_stage": "stable-core-polished",
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
