from __future__ import annotations

import uuid
from typing import Tuple

from ai_factory.router_v2.router_v2_store import list_models, upsert_model
from ai_factory.memory.memory_embeddings import add_to_memory


def compute_reward(prev_score: float, new_score: float, alpha: float = 1.0) -> float:
    return (new_score - prev_score) * alpha


def adjust_router_weight(model_name: str, reward: float) -> float:
    """Adjust the Router V2 registry weight for a model based on reward.

    Positive rewards increase weight; negatives decrease. Clamp to [0.5, 2.0].
    Returns the updated weight.
    """
    models = {m.model_name: m for m in list_models()}
    cur = float(models.get(model_name).weight) if model_name in models else 1.0
    new_w = max(0.5, min(2.0, cur + 0.05 * reward))
    upsert_model(model_name, None, new_w)
    return new_w


def inject_memory_snippet(model_name: str, task_type: str, reward: float, reason: str = "") -> None:
    rid = f"eval9:{uuid.uuid4()}"
    snippet = (
        "[EVAL v9]\n"
        f"model: {model_name}\n"
        f"task_type: {task_type}\n"
        f"reward: {reward:+.2f}\n"
        f"reason: {reason or 'adaptive update'}"
    )
    add_to_memory(rid, snippet)

