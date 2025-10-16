from __future__ import annotations

from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Path, Query

from ai_factory.orchestrator.orchestrator_agent import run as run_orch, status as get_status, history as get_history
from ai_factory.tests.stress_tester import run_stress_test
import asyncio


router = APIRouter(tags=["orchestrator"])  # prefix is added in main.py


@router.post("/run")
def run(payload: Dict[str, Any]):
    goal = (payload or {}).get("goal", "").strip()
    if not goal:
        raise HTTPException(status_code=400, detail="goal must not be empty")
    max_attempts = payload.get("max_attempts") if payload else None
    deploy = bool(payload.get("deploy", False)) if payload else False
    return run_orch(goal, max_attempts=max_attempts, deploy=deploy)


@router.get("/status")
def status_root():
    return {"status": "orchestrator online"}


@router.get("/status/{run_id}")
def status(run_id: int = Path(..., ge=1)):
    return get_status(run_id)


@router.get("/history")
def history(limit: int = Query(10, ge=1, le=100)):
    return get_history(limit=limit)


@router.get("/stress")
async def stress_test(n: int = Query(5, ge=1, le=50)):
    """
    Launches n test deployments, verifies them, and cleans them up automatically.
    Returns performance metrics and logs results to deployments/stress_test.log.
    """
    result = await run_stress_test(n)
    return {"status": "ok", "report": result}
