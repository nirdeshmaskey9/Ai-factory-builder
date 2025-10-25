from __future__ import annotations

from fastapi import APIRouter, Path
from typing import Dict, Any

from ai_factory.orchestrator.orchestrator_store import get_run
from ai_factory.orchestrator.orchestrator_agent import run as run_orchestrator


router = APIRouter(prefix="/rerun", tags=["Rerun"])


@router.post("/{run_id}")
def rerun(run_id: int = Path(..., ge=1)) -> Dict[str, Any]:
    row = get_run(run_id)
    if not row:
        return {"status": "error", "detail": "Goal not found"}
    goal = row.goal
    result = run_orchestrator(goal, max_attempts=2, deploy=False)
    return {"status": "ok", "new_run_id": result.get("run_id")}

