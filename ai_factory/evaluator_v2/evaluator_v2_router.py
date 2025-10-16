from __future__ import annotations

from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Query

from ai_factory.evaluator_v2.evaluator_v2_agent import create_reward, stats as reward_stats, trends as reward_trends, learn as apply_learn


router = APIRouter(prefix="/evaluator", tags=["evaluator_v2"])


@router.post("/reward")
def reward(payload: Dict[str, Any]):
    if not payload or not payload.get("model_name") or not payload.get("task_type"):
        raise HTTPException(status_code=400, detail="model_name and task_type are required")
    score_delta = float(payload.get("score_delta", 0.0))
    return create_reward(payload["model_name"], payload["task_type"], score_delta, payload.get("notes", ""))


@router.get("/reward/stats")
def stats():
    return reward_stats()


@router.get("/reward/trends")
def trends(limit: int = Query(10, ge=1, le=200)):
    return reward_trends(limit=limit)


@router.post("/learn")
def learn():
    return apply_learn()

