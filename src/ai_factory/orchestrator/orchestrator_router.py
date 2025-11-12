from __future__ import annotations

from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Path, Query
from typing import Optional
import os
import json

from ai_factory.orchestrator.orchestrator_agent import run as run_orch, status as get_status, history as get_history
from ai_factory.orchestrator.orchestrator_store import list_runs, get_run_steps, get_run_summary
from tests.stress_tester import run_stress_test
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
def history(limit: int = Query(10, ge=1, le=100), status: Optional[str] = Query(None), sort: str = Query("desc")):
    rows = list_runs(limit=limit, status=status, sort=sort)
    out = []
    for r in rows:
        # Try to enrich with duration and artifact paths
        run_report_path = os.path.join("logs", "orchestrator", f"run_{r.id}.json")
        duration = None
        if os.path.exists(run_report_path):
            try:
                with open(run_report_path, "r", encoding="utf-8") as f:
                    j = json.load(f)
                    duration = j.get("duration_sec")
            except Exception:
                pass
        out.append({
            "run_id": r.id,
            "goal": r.goal,
            "status": r.status,
            "score": r.evaluation_score,
            "attempt": r.attempt,
            "duration_sec": duration,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            "report_path": run_report_path if os.path.exists(run_report_path) else None,
            "supervisor_report_path": os.path.join("logs", "supervisor", f"report_{r.id}.json"),
        })
    return out


@router.get("/stress")
async def stress_test(n: int = Query(5, ge=1, le=50)):
    """
    Launches n test deployments, verifies them, and cleans them up automatically.
    Returns performance metrics and logs results to deployments/stress_test.log.
    """
    result = await run_stress_test(n)
    return {"status": "ok", "report": result}


@router.get("/steps/{run_id}")
def run_steps(run_id: int = Path(..., ge=1)):
    steps = get_run_steps(run_id)
    return [
        {
            "id": s.id,
            "step_name": s.step_name,
            "step_status": s.step_status,
            "log_path": s.log_path or None,
            "timestamp": s.timestamp.isoformat() if s.timestamp else None,
        }
        for s in steps
    ]


@router.get("/summary/{run_id}")
def run_summary(run_id: int = Path(..., ge=1)):
    summary = get_run_summary(run_id)
    if summary.get("not_found"):
        raise HTTPException(status_code=404, detail="run not found")
    return summary
