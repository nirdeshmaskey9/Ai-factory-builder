from __future__ import annotations

from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Query

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

