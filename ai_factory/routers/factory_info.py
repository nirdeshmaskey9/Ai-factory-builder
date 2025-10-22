from __future__ import annotations

from fastapi import APIRouter
import os


router = APIRouter(prefix="/factory", tags=["Factory"])


@router.get("/info")
def factory_info():
    return {
        "name": "AI Factory",
        "version": os.getenv("FACTORY_VERSION", "v1.4.3-quicklaunch"),
        "status": "online",
        "banner": "AI Factory v1.3-gpt4o-builder — Live Planner Active",
        "healthy": True,
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

