from __future__ import annotations

from fastapi import APIRouter
import os
from pathlib import Path


router = APIRouter(prefix="/factory", tags=["Factory"])


@router.get("/info")
def factory_info():
    # Prefer VERSION file, then env var, then default
    version_file = Path("VERSION")
    version = None
    try:
        if version_file.exists():
            version = version_file.read_text(encoding="utf-8").strip()
    except Exception:
        version = None
    version = os.getenv("FACTORY_VERSION", version or "v2.0-cognitive-engine")
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
        "banner": f"AI Factory {version} - Cognitive Engine Active",
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
