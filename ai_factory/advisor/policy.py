from __future__ import annotations

from typing import Dict, Optional


def guess_role(goal: str, domain: Optional[str]) -> str:
    g = (goal or "").lower()
    d = (domain or "").lower() if domain else ""
    text = f"{g} {d}"
    if any(k in text for k in ["summary", "context", "recall", "memory"]):
        return "memory"
    if any(k in text for k in ["task", "run", "rename", "fix", "execute"]):
        return "executor"
    if any(k in text for k in ["code", "dev", "build", "api", "plan", "design"]):
        return "strategist"
    return "strategist"


def decide(
    goal: str,
    domain: Optional[str],
    hint: Optional[str],
    privacy_strict: bool,
    local_available: Dict[str, bool],
    model_perf: Optional[Dict[str, float]] = None,
) -> Dict[str, str]:
    role = guess_role(goal, domain)

    # If hint explicitly asks cloud/local, bias toward it if healthy
    if hint:
        h = hint.lower()
        if h in ("local", "cloud", "openai"):
            if h == "local" and local_available.get(role, False):
                return {"backend": "local", "role": role}
            if h in ("cloud", "openai"):
                return {"backend": "openai", "role": role}

    # Privacy strict -> prefer local if available
    if privacy_strict and local_available.get(role, False):
        return {"backend": "local", "role": role}

    # Otherwise choose healthy local, fallback to openai
    if local_available.get(role, False):
        return {"backend": "local", "role": role}
    return {"backend": "openai", "role": role}

