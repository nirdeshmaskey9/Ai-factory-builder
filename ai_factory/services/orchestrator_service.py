from __future__ import annotations

import json
from typing import Optional


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


def success_threshold() -> float:
    return 0.6


def max_attempts_or_default(user_value: Optional[int]) -> int:
    return user_value if (isinstance(user_value, int) and user_value > 0) else 2


def should_repair(prev_score: float, new_score: float, attempt: int, max_attempts: int) -> bool:
    if attempt >= max_attempts:
        return False
    if new_score < success_threshold() and new_score >= prev_score:
        return True
    return False


def make_orch_snippet(goal: str, model: str, score: float, status: str, endpoint: Optional[str] = None) -> str:
    return (
        "[ORCH v10]\n"
        f"goal: \"{goal}\"\n"
        f"model: {model}\n"
        f"score: {score:.2f} status: {status}\n"
        f"deployment: {endpoint or 'none'}"
    )

