from __future__ import annotations

import json
from typing import Optional
import uuid

import ai_factory.services.evaluator_v2_service as eval_v2_svc
from ai_factory.memory.memory_embeddings import add_to_memory


def choose_primary_task_type(plan_json: str) -> str:
    try:
        plan = json.loads(plan_json)
        steps = plan.get("steps", [])
        texts = " ".join(s.get("action", "").lower() for s in steps)
        if any(k in texts for k in ("ui", "design")):
            return "design"
        if any(k in texts for k in ("deploy", "deployer")):
            return "deployment"
        if any(k in texts for k in ("test", "pytest", "quality")):
            return "testing"
        if any(k in texts for k in ("code", "python", "script")):
            return "coding"
    except Exception:
        pass
    return "planning"


def success_threshold(task_type: str = "general") -> float:
    """Adaptive success threshold based on average reward (Phase 10.1).

    - Early/low-reward phases → lenient (0.45)
    - Stable/high-reward phases → strict (0.65)
    - Otherwise adaptive midpoint (0.55)
    Also logs an adaptive-threshold memory snippet.
    """
    try:
        avg_reward = float(eval_v2_svc.get_average_reward())
    except Exception:
        avg_reward = 0.0

    if avg_reward < 0.3:
        threshold = 0.45
    elif avg_reward > 0.6:
        threshold = 0.65
    else:
        threshold = 0.55

    # Log adaptive behavior into memory
    rid = f"orch-thresh:{uuid.uuid4()}"
    add_to_memory(rid, f"[ORCH v10.1] Adaptive success threshold = {threshold:.2f} (avg_reward={avg_reward:.2f})")

    return threshold


def max_attempts_or_default(user_value: Optional[int]) -> int:
    return user_value if (isinstance(user_value, int) and user_value > 0) else 2


def should_repair(prev_score: float, new_score: float, attempt: int, max_attempts: int) -> bool:
    # Trigger repair if in "learning zone" and attempts remain
    if attempt >= max_attempts:
        return False
    return 0.3 <= float(new_score) < success_threshold()


def make_orch_snippet(goal: str, model: str, score: float, status: str, endpoint: Optional[str] = None) -> str:
    return (
        "[ORCH v10]\n"
        f"goal: \"{goal}\"\n"
        f"model: {model}\n"
        f"score: {score:.2f} status: {status}\n"
        f"deployment: {endpoint or 'none'}"
    )
