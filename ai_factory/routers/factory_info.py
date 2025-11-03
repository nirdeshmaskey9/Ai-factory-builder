from __future__ import annotations

from fastapi import APIRouter, Request
import os
from pathlib import Path


router = APIRouter(prefix="/factory", tags=["Factory"])


@router.get("/info")
def factory_info(request: Request):
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
    # Orchestrator stats
    try:
        from ai_factory.orchestrator.orchestrator_store import list_runs
        runs = list_runs(limit=1, sort="desc")
        latest_run_id = runs[0].id if runs else None
        total_runs = len(list_runs(limit=1000))  # lightweight scan
    except Exception:
        latest_run_id = None
        total_runs = 0

    # Phase/version from ai_factory.version if available
    try:
        from ai_factory.version import PHASE as _PHASE
    except Exception:
        _PHASE = None

    info = {
        "name": "AI Factory",
        "version": version,
        "release_stage": "stable-core-polished",
        "status": "online",
        "banner": f"AI Factory {version} - Cognitive Engine Active",
        "healthy": True,
        "phase": _PHASE or "",
        "templates": templates,
        "latest_run_id": latest_run_id,
        "total_runs": total_runs,
        "memory_enabled": True,
        "memory_counts": (lambda: __import__('ai_factory.memory.memory_agent', fromlist=['stats']).stats())(),
    }
    # Advisor flags
    try:
        info["advisor_enabled"] = (os.getenv("AI_FACTORY_ADVISOR_ENABLED", "true").lower() == "true")
        info["cloud_backend"] = os.getenv("AI_FACTORY_CLOUD_BACKEND", "openai")
        info["local_models"] = [
            os.getenv("AI_FACTORY_LOCAL_STRATEGIST_MODEL", "mistral:7b-q4_K_M"),
            os.getenv("AI_FACTORY_LOCAL_MEMORY_MODEL", "phi3:3b-q4"),
            os.getenv("AI_FACTORY_LOCAL_EXECUTION_MODEL", "phi:mini"),
        ]
        # Prefer live status from trio manager if available
        tm = getattr(request.app.state, 'trio_manager', None)
        if tm and getattr(tm, 'health_map', None):
            info["local_trio_health"] = {k: {"healthy": bool(v.get('healthy')), "model": v.get('model')} for k, v in tm.health_map.items()}
        else:
            # Use advisor service unified health check
            from ai_factory.advisor.advisor_service import verify_local_health
            info["local_trio_health"] = verify_local_health().get("roles", {})
    except Exception:
        pass
    return info


@router.get("/health")
def factory_health():
    return {
        "db": "OK",
        "planner": "OK",
        "deployer": "OK",
        "evaluator": "Partial (some routes missing)",
        "summary": "Operational",
    }
