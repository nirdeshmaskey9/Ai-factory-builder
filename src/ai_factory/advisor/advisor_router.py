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
    # Central trio and unified host
    try:
        from ai_factory.advisor.local_trio import local_trio, as_registry
        trio = dict(local_trio)
        reg = as_registry()
    except Exception:
        trio = {
            "strategist": os.getenv("AI_FACTORY_LOCAL_STRATEGIST_MODEL", "qwen2:1.5b-instruct-q4_K_M"),
            "memory": os.getenv("AI_FACTORY_LOCAL_MEMORY_MODEL", "mistral:7b-instruct-v0.3-q4_K_M"),
            "executor": os.getenv("AI_FACTORY_LOCAL_EXECUTION_MODEL", "phi3:mini-4k-instruct-q4_K_M"),
        }
        reg = {"trio": {r: {"model": m, "purpose": ""} for r, m in trio.items()}}
    host = (os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434") or "http://127.0.0.1:11434").rstrip("/")
    # Use advisor_service verify to compute health in one call
    health = verify_local_health().get("roles", {})
    for role, model in trio.items():
        out["locals"].append({
            "role": role,
            "model": model,
            "url": host,
            "purpose": reg.get("trio", {}).get(role, {}).get("purpose", ""),
            "healthy": bool(health.get(role, {}).get("healthy")),
        })
    return out


@router.get("/trio_health")
def trio_health(request: Request) -> Dict[str, Any]:
    tm = getattr(request.app.state, "trio_manager", None)
    if tm and getattr(tm, "health_map", None):
        roles = tm.health_map
        # If any not yet healthy, perform a quick synchronous probe via POST only
        if any(not bool(v.get("healthy")) for v in roles.values()):
            try:
                import os as _os
                import httpx as _hx
                host = (_os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434") or "http://127.0.0.1:11434").rstrip("/")
                with _hx.Client(timeout=float(_os.getenv("AI_FACTORY_LOCAL_TIMEOUT", "2") or 2)) as c:
                    for role, state in roles.items():
                        model = state.get("model") or ""
                        try:
                            r = c.post(f"{host}/api/generate", json={"model": model, "prompt": "ping", "stream": False})
                            roles[role]["healthy"] = (r.status_code == 200)
                        except Exception:
                            roles[role]["healthy"] = False
            except Exception:
                pass
        return {"roles": roles}
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
