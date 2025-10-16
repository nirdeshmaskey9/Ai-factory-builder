from __future__ import annotations

from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Path, Query

from ai_factory.orchestrator.orchestrator_agent import run as run_orch, status as get_status, history as get_history


router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])


@router.post("/run")
def run(payload: Dict[str, Any]):
    goal = (payload or {}).get("goal", "").strip()
    if not goal:
        raise HTTPException(status_code=400, detail="goal must not be empty")
    max_attempts = payload.get("max_attempts") if payload else None
    deploy = bool(payload.get("deploy", False)) if payload else False
    return run_orch(goal, max_attempts=max_attempts, deploy=deploy)


@router.get("/status/{run_id}")
def status(run_id: int = Path(..., ge=1)):
    return get_status(run_id)


@router.get("/history")
def history(limit: int = Query(10, ge=1, le=100)):
    return get_history(limit=limit)

