from __future__ import annotations

from typing import Any, Dict

from ai_factory.evaluator_v2.evaluator_v2_store import log_reward, recent_rewards, avg_reward_per_model
from ai_factory.services.evaluator_v2_service import adjust_router_weight, inject_memory_snippet


def create_reward(model_name: str, task_type: str, score_delta: float, notes: str = "") -> Dict[str, Any]:
    reward = float(score_delta)  # direct scale; could be tuned
    log_id = log_reward(model_name=model_name, task_type=task_type, score_delta=score_delta, reward=reward, notes=notes)
    new_weight = adjust_router_weight(model_name, reward)
    inject_memory_snippet(model_name, task_type, reward, notes)
    return {"reward_id": log_id, "model_name": model_name, "task_type": task_type, "reward": reward, "updated_weight": new_weight}


def stats() -> Dict[str, Any]:
    pairs = avg_reward_per_model()
    return {"averages": [{"model_name": m, "avg_reward": avg} for m, avg in pairs]}


def trends(limit: int = 10) -> Dict[str, Any]:
    rows = recent_rewards(limit=limit)
    return {
        "recent": [
            {
                "id": r.id,
                "model_name": r.model_name,
                "task_type": r.task_type,
                "score_delta": r.score_delta,
                "reward": r.reward,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            }
            for r in rows
        ]
    }


def learn() -> Dict[str, Any]:
    # Simple learning: re-apply averages once to nudge weights
    applied = []
    for m, avg in avg_reward_per_model():
        w = adjust_router_weight(m, avg)
        applied.append({"model_name": m, "avg_reward": avg, "weight": w})
    return {"applied": applied}

