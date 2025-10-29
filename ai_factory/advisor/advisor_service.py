from __future__ import annotations

from typing import Dict, Optional, Any
import os
import time
import httpx

from ai_factory.advisor import policy
from ai_factory.advisor.context_filter import select_safe_snippets
from ai_factory.memory.memory_agent import stats as memory_stats
from ai_factory.memory.memory_agent import store_memory


def _env(key: str, default: Optional[str] = None) -> str | None:
    v = os.getenv(key)
    return v if v is not None else default


def _ping_generate(host: str, model: str, timeout: float) -> bool:
    try:
        with httpx.Client(timeout=timeout) as c:
            v = c.get(host.rstrip("/") + "/api/version")
            if v.status_code != 200:
                return False
            r = c.post(host.rstrip("/") + "/api/generate", json={"model": model, "prompt": "ping", "stream": False})
            if r.status_code != 200:
                return False
            try:
                j = r.json()
                return bool(j)
            except Exception:
                return bool(getattr(r, "text", ""))
    except Exception:
        return False


def verify_local_health() -> Dict[str, Any]:
    """Check unified local trio health by model name against one Ollama host.

    Returns: {"roles": {role: {"healthy": bool, "model": str}}}
    with simple exponential backoff tolerance (10s, 20s, 30s) per role.
    """
    host = (_env("OLLAMA_HOST", "http://127.0.0.1:11434") or "http://127.0.0.1:11434").rstrip("/")
    roles = {
        "strategist": _env("AI_FACTORY_LOCAL_STRATEGIST_MODEL", "llama3.1:8b") or "llama3.1:8b",
        "memory": _env("AI_FACTORY_LOCAL_MEMORY_MODEL", "qwen2.5:1.5b") or "qwen2.5:1.5b",
        "executor": _env("AI_FACTORY_LOCAL_EXECUTION_MODEL", "phi3:mini") or "phi3:mini",
    }
    to = 2.0
    try:
        to = float(_env("AI_FACTORY_LOCAL_TIMEOUT", "2") or 2)
    except Exception:
        pass
    # Speed up under pytest to avoid slow startups
    if os.getenv("PYTEST_CURRENT_TEST"):
        to = min(to, 0.2)
    base_delay = 10
    try:
        base_delay = int(_env("AI_FACTORY_HEALTH_BACKOFF_BASE", "10") or 10)
    except Exception:
        pass
    out: Dict[str, Dict[str, Any]] = {}
    for role, model in roles.items():
        healthy = False
        delays = (base_delay, base_delay * 2, base_delay * 3)
        if os.getenv("PYTEST_CURRENT_TEST"):
            delays = (0,)
        for delay in delays:
            healthy = _ping_generate(host, model, to)
            if healthy:
                break
            try:
                # Sleep between retries without blocking tests too long
                import time as _t
                _t.sleep(0 if os.getenv("PYTEST_CURRENT_TEST") else delay)
            except Exception:
                pass
        out[role] = {"healthy": healthy, "model": model}
    return {"roles": out}


def _local_map() -> Dict[str, Dict[str, str]]:
    # Kept for backward-compat callers; use unified host for URLs
    host = (_env("OLLAMA_HOST", "http://127.0.0.1:11434") or "http://127.0.0.1:11434").rstrip("/")
    return {
        "strategist": {
            "model": _env("AI_FACTORY_LOCAL_STRATEGIST_MODEL", "mistral:7b-q4_K_M") or "mistral:7b-q4_K_M",
            "url": host,
        },
        "memory": {
            "model": _env("AI_FACTORY_LOCAL_MEMORY_MODEL", "phi3:3b-q4") or "phi3:3b-q4",
            "url": host,
        },
        "executor": {
            "model": _env("AI_FACTORY_LOCAL_EXECUTION_MODEL", "phi:mini") or "phi:mini",
            "url": host,
        },
    }


def startup_probe() -> None:
    """Log local trio health at startup for diagnostics."""
    try:
        local = _local_map()
        urls = {role: cfg["url"] for role, cfg in local.items()}
        res = verify_local_health()
        msg = " | ".join([f"{role.capitalize()}: {'Healthy ✅' if ok else 'Down ❌'}" for role, ok in res.items()])
        print(f"[Advisor] {msg}")
    except Exception:
        pass


def route_task(goal: str, domain: Optional[str], hint: Optional[str], topk: int = 3) -> Dict[str, str]:
    enabled = (_env("AI_FACTORY_ADVISOR_ENABLED", "true") or "true").lower() == "true"
    privacy_strict = (_env("AI_FACTORY_PRIVACY_STRICT", "true") or "true").lower() == "true"
    if not enabled:
        # default to cloud strategist
        return {
            "backend": "openai",
            "role": "strategist",
            "model": _env("AI_FACTORY_CLOUD_MODEL", "gpt-4o") or "gpt-4o",
            "url": "",
            "reason": "advisor disabled; default cloud",
        }

    local = _local_map()
    timeout = float(_env("AI_FACTORY_LOCAL_TIMEOUT", "5") or "5")
    # health pings via unified host using model
    host = (_env("OLLAMA_HOST", "http://127.0.0.1:11434") or "http://127.0.0.1:11434").rstrip("/")
    availability = {role: _ping_generate(host, cfg["model"], timeout) for role, cfg in local.items()}

    # Simple performance stub (future): could read aggregates from model_usage
    perf = {}

    decision = policy.decide(goal, domain, hint, privacy_strict, availability, perf)
    role = decision["role"]
    if decision["backend"] == "local":
        model = local[role]["model"]
        url = (_env("OLLAMA_HOST", "http://127.0.0.1:11434") or "http://127.0.0.1:11434").rstrip("/")
        backend = "local"
        reason = f"local {role} available; privacy_strict={privacy_strict}"
    else:
        model = _env("AI_FACTORY_CLOUD_MODEL", "gpt-4o") or "gpt-4o"
        url = ""
        backend = "openai"
        reason = "fallback to cloud"

    # Minimal context preview for decision trace (redacted & top-k)
    try:
        s = memory_stats()
        # Not fetching actual rows here to avoid heavy joins in service
        ctx = select_safe_snippets([], topk)
    except Exception:
        ctx = []

    # Record a lightweight memory entry for observability
    try:
        store_memory(None, goal=f"Advisor decision for: {goal[:60]}", summary=f"{backend}/{model} ({role})", tags=["advisor_decision", role], score=None)
    except Exception:
        pass

    return {
        "backend": backend,
        "role": role,
        "model": model,
        "url": url,
        "reason": reason,
    }
