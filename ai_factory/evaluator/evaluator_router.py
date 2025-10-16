from __future__ import annotations

from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Query

from ai_factory.evaluator.evaluator_agent import evaluate
from ai_factory.evaluator.evaluator_store import get_recent


router = APIRouter(prefix="/evaluator", tags=["evaluator"])


@router.post("/evaluate")
def run(payload: Dict[str, Any]):
    sess_id = payload.get("session_id") if payload else None
    goal = (payload or {}).get("goal")
    try:
        return evaluate(session_id=sess_id, goal=goal)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))


@router.get("/scores")
def scores(limit: int = Query(10, ge=1, le=100)):
    rows = get_recent(limit=limit)
    return [
        {
            "id": r.id,
            "session_id": r.session_id,
            "goal": r.goal,
            "score": r.score,
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
        text = (r.feedback or "")
        if len(text) > 180:
            text = text[:180] + "..."
        out.append({
            "id": r.id,
            "session_id": r.session_id,
            "goal": r.goal,
            "status": r.status,
            "summary": text,
        })
    return out

