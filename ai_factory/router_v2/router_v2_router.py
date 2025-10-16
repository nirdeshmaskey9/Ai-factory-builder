from __future__ import annotations

from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Query

from ai_factory.router_v2.router_v2_store import list_models, recent_logs, upsert_model
from ai_factory.router_v2.router_v2_agent import route_task


router = APIRouter(prefix="/router", tags=["router_v2"])


@router.get("/models")
def models():
    rows = list_models()
    return [
        {
            "model_name": r.model_name,
            "capabilities": r.capabilities,
            "weight": r.weight,
            "avg_latency_ms": r.avg_latency_ms,
            "avg_cost": r.avg_cost,
            "success_rate": r.success_rate,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        }
        for r in rows
    ]


@router.post("/route")
def route(payload: Dict[str, Any]):
    task_type = (payload or {}).get("task_type", "general")
    meta = (payload or {}).get("meta")
    return route_task(task_type, meta)


@router.post("/update")
def update(payload: Dict[str, Any]):
    name = (payload or {}).get("model_name")
    if not name:
        raise HTTPException(status_code=400, detail="model_name is required")
    caps = payload.get("capabilities")
    weight = payload.get("weight")
    upsert_model(name, caps, weight)
    return {"status": "ok"}


@router.get("/logs")
def logs(limit: int = Query(10, ge=1, le=200)):
    rows = recent_logs(limit=limit)
    return [
        {
            "id": r.id,
            "task_type": r.task_type,
            "model_name": r.model_name,
            "duration_ms": r.duration_ms,
            "score": r.score,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
        }
        for r in rows
    ]

