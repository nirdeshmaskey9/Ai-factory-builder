from __future__ import annotations

from fastapi import APIRouter, Request
from typing import Any, Dict
import os
import httpx

from ai_factory.advisor.advisor_service import route_task, verify_local_health


router = APIRouter(prefix="/advisor", tags=["advisor"])


@router.post("/route")
def route(payload: Dict[str, Any]) -> Dict[str, Any]:
    goal = str(payload.get("goal") or "")
    domain = payload.get("domain")
    hint = payload.get("hint")
    topk = int(os.getenv("AI_FACTORY_CONTEXT_TOPK", "3"))
    d = route_task(goal, domain, hint, topk)
    return d


def _health(url: str, timeout: float) -> bool:
    try:
        with httpx.Client(timeout=timeout) as c:
            r = c.get(url.rstrip("/") + "/api/tags")
            return r.status_code < 500
    except Exception:
        return False


@router.get("/models")
def models() -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "cloud_backend": os.getenv("AI_FACTORY_CLOUD_BACKEND", "openai"),
        "cloud_model": os.getenv("AI_FACTORY_CLOUD_MODEL", "gpt-4o"),
        "locals": [],
    }
    trio = {
        "strategist": (os.getenv("AI_FACTORY_LOCAL_STRATEGIST_MODEL", "mistral:7b-q4_K_M"), os.getenv("AI_FACTORY_LOCAL_STRATEGIST_URL", "http://127.0.0.1:11434")),
        "memory": (os.getenv("AI_FACTORY_LOCAL_MEMORY_MODEL", "phi3:3b-q4"), os.getenv("AI_FACTORY_LOCAL_MEMORY_URL", "http://127.0.0.1:11435")),
        "executor": (os.getenv("AI_FACTORY_LOCAL_EXECUTION_MODEL", "phi:mini"), os.getenv("AI_FACTORY_LOCAL_EXECUTION_URL", "http://127.0.0.1:11436")),
    }
    timeout = float(os.getenv("AI_FACTORY_LOCAL_TIMEOUT", "5"))
    for role, (model, url) in trio.items():
        out["locals"].append({
            "role": role,
            "model": model,
            "url": url,
            "healthy": _health(url, timeout),
        })
    return out


@router.get("/trio_health")
def trio_health(request: Request) -> Dict[str, Any]:
    tm = getattr(request.app.state, "trio_manager", None)
    if tm and getattr(tm, "health_map", None):
        return {"roles": tm.health_map}
    return verify_local_health()


@router.get("/stats")
def stats() -> Dict[str, Any]:
    # Defer to /analytics/models for aggregates; here just echo env
    return {
        "advisor_enabled": os.getenv("AI_FACTORY_ADVISOR_ENABLED", "true"),
        "privacy_strict": os.getenv("AI_FACTORY_PRIVACY_STRICT", "true"),
        "context_topk": int(os.getenv("AI_FACTORY_CONTEXT_TOPK", "3")),
    }


@router.post("/reload")
def reload_env() -> Dict[str, Any]:
    # No-op placeholder; environment is read dynamically
    return {"reloaded": True}
