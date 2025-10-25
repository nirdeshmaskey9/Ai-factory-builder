from __future__ import annotations

from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Query, Path
import os
import json

from ai_factory.supervisor.supervisor_agent import run_supervisor
from ai_factory.supervisor.supervisor_store import get_recent


router = APIRouter(prefix="/supervisor", tags=["supervisor"])


@router.post("/run")
def run(payload: Dict[str, Any]):
    goal = (payload or {}).get("goal", "").strip()
    if not goal:
        raise HTTPException(status_code=400, detail="goal must not be empty")
    return run_supervisor(goal)


@router.get("/status")
def status(limit: int = Query(10, ge=1, le=100)):
    rows = get_recent(limit=limit)
    return [
        {
            "id": r.id,
            "request_id": r.request_id,
            "goal": r.goal,
            "status": r.status,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
        }
        for r in rows
    ]


@router.get("/history")
def history(limit: int = Query(10, ge=1, le=100)):
    rows = get_recent(limit=limit)
    out = []
    for r in rows:
        summary = (r.result or "").strip()
        if len(summary) > 180:
            summary = summary[:180] + "..."
        out.append({
            "id": r.id,
            "request_id": r.request_id,
            "goal": r.goal,
            "status": r.status,
            "summary": summary,
        })
    return out


@router.get("/report/{run_id}")
def report(run_id: int = Path(..., ge=1)):
    """Returns supervisor report JSON for a given orchestrator run if available."""
    path = os.path.join("logs", "supervisor", f"report_{run_id}.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="report not found")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception:
        raise HTTPException(status_code=500, detail="unable to read report")
