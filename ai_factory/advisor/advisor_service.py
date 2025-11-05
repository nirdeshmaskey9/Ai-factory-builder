from __future__ import annotations

from typing import Dict, Optional, Any
import os
import time
import httpx

from ai_factory.advisor import policy
from ai_factory.advisor.context_filter import select_safe_snippets
from ai_factory.memory.memory_agent import stats as memory_stats
from ai_factory.memory.memory_agent import store_memory
from ai_factory import config_runtime_flags as r

try:
    from ai_factory.rag import rag_service as _rag
except Exception:
    _rag = None


def _env(key: str, default: Optional[str] = None) -> str | None:
    v = os.getenv(key)
    return v if v is not None else default


def _ping_generate(host: str, model: str, timeout: float) -> bool:
    try:
        with httpx.Client(timeout=timeout) as c:
            # Require daemon version AND simple generate to count as healthy (advisor strict path)
            v = c.get(host.rstrip("/") + "/api/version")
            if v.status_code != 200:
                return False
            r = c.post(host.rstrip("/") + "/api/generate", json={"model": model, "prompt": "ping", "stream": False})
            return r.status_code == 200
    except Exception:
        return False


def verify_local_health(urls: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Check unified local trio health by model name against one Ollama host.

    Returns: {"roles": {role: {"healthy": bool, "model": str}}}
    with simple exponential backoff tolerance (10s, 20s, 30s) per role.
    """
    host = (_env("OLLAMA_HOST", "http://127.0.0.1:11434") or "http://127.0.0.1:11434").rstrip("/")
    # Single source of truth for trio
    try:
        from ai_factory.advisor.local_trio import local_trio
        roles = dict(local_trio)
    except Exception:
        roles = {
            "strategist": _env("AI_FACTORY_LOCAL_STRATEGIST_MODEL", "phi3:medium") or "phi3:medium",
            "memory": _env("AI_FACTORY_LOCAL_MEMORY_MODEL", "mistral") or "mistral",
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
    out_roles: Dict[str, Dict[str, Any]] = {}
    for role, model in roles.items():
        healthy = False
        delays = (base_delay, base_delay * 2, base_delay * 3)
        if os.getenv("PYTEST_CURRENT_TEST"):
            delays = (0,)
        if urls is not None:
            # Back-compat path: treat provided mapping as direct endpoints; only GET /api/version
            try:
                import httpx
                with httpx.Client(timeout=to) as c:
                    u = (urls.get(role) or host).rstrip("/")
                    r = c.get(u + "/api/version")
                    healthy = (r.status_code == 200)
            except Exception:
                healthy = False
        else:
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
        out_roles[role] = {"healthy": healthy, "model": model}
    # Back-compat: if caller provided explicit URLs mapping, return role->bool
    if urls is not None:
        return {k: bool(v.get("healthy")) for k, v in out_roles.items()}  # type: ignore[return-value]
    return {"roles": out_roles}


def _local_map() -> Dict[str, Dict[str, str]]:
    # Use unified host for all roles; models from central trio
    host = (_env("OLLAMA_HOST", "http://127.0.0.1:11434") or "http://127.0.0.1:11434").rstrip("/")
    try:
        from ai_factory.advisor.local_trio import local_trio
        m = dict(local_trio)
    except Exception:
        m = {
            "strategist": _env("AI_FACTORY_LOCAL_STRATEGIST_MODEL", "phi3:medium") or "phi3:medium",
            "memory": _env("AI_FACTORY_LOCAL_MEMORY_MODEL", "mistral") or "mistral",
            "executor": _env("AI_FACTORY_LOCAL_EXECUTION_MODEL", "phi3:mini") or "phi3:mini",
        }
    return {
        "strategist": {"model": m["strategist"], "url": host},
        "memory": {"model": m["memory"], "url": host},
        "executor": {"model": m["executor"], "url": host},
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

    # Optional RAG context fetch (Phase 4.0)
    try:
        rag_snips = []
        if r.rag_enabled and _rag is not None and goal:
            rag_snips = [x.get("text", "")[:400] for x in (_rag.retrieve(goal, top_k=5) or [])]
            if rag_snips:
                try:
                    store_memory(None, goal=f"RAG ctx for: {goal[:60]}", summary="\n---\n".join(rag_snips), tags=["rag_ctx", "advisor"], score=None)
                except Exception:
                    pass
    except Exception:
        pass

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

    out = {
        "backend": backend,
        "role": role,
        "model": model,
        "url": url,
        "reason": reason,
    }
    # Advisor fusion preview (caps and stitching)
    try:
        # memory preview via safe selection
        mem_preview_list = select_safe_snippets([], topk)
        mem_ctx = "\n".join(mem_preview_list)[:512]
        rag_ctx = "\n".join(rag_snips)[:512] if rag_snips else ""
        out["context_preview"] = {
            "memory_context": mem_ctx,
            "rag_context": rag_ctx,
            "stitched": f"{mem_ctx}\n\n---\n\n{rag_ctx}".strip(),
        }
    except Exception:
        pass
    try:
        g = (goal or "").lower()
        if "bridge" in g or "chat" in g:
            out["advisor_tag"] = "hybrid_reasoning"
    except Exception:
        pass
    return out
