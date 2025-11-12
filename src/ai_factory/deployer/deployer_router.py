from __future__ import annotations

from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Path, Query

from ai_factory.deployer.deployer_agent import deploy as do_deploy, status as get_status, rollback as do_rollback
from ai_factory.deployer.deployer_store import get_recent


router = APIRouter(prefix="/deployer", tags=["deployer"])


@router.post("/deploy")
def deploy(payload: Dict[str, Any]):
    sess_id = payload.get("session_id") if payload else None
    goal = (payload or {}).get("goal")
    try:
        return do_deploy(sess_id, goal)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))


@router.get("/status/{deployment_id}")
def status(deployment_id: int = Path(..., ge=1)):
    try:
        return get_status(deployment_id)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))


@router.get("/list")
def list_deployments(limit: int = Query(10, ge=1, le=100)):
    rows = get_recent(limit=limit)
    return [
        {
            "id": r.id,
            "goal": r.goal,
            "port": r.port,
            "endpoint": r.endpoint,
            "status": r.status,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
        }
        for r in rows
    ]


@router.post("/rollback")
def rollback(payload: Dict[str, Any]):
    dep_id = (payload or {}).get("deployment_id")
    if not isinstance(dep_id, int):
        raise HTTPException(status_code=400, detail="deployment_id must be an integer")
    try:
        return do_rollback(dep_id)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))

