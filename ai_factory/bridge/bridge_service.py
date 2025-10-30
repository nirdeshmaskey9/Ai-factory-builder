from __future__ import annotations

import os
import re
import time
from typing import Dict, Any, List, Optional
from pathlib import Path

from ai_factory.memory import memory_agent
from ai_factory.bridge.chatgpt_proxy import call_chatgpt
from ai_factory.bridge.response_manager import integrate_response


def _redact_private(text: str) -> (str, List[str]):
    redacted: List[str] = []
    out = text or ""
    # OpenAI-style keys
    out2 = re.sub(r"sk-[A-Za-z0-9\-_]{10,}", "sk-***REDACTED***", out)
    if out2 != out:
        redacted.append("api_keys")
        out = out2
    # Windows personal paths
    out2 = re.sub(r"[A-Za-z]:\\\\Users\\\\[A-Za-z0-9_.-]+\\\\[^\s\"]+", r"C:\\Users\\***REDACTED***\\...", out)
    if out2 != out:
        redacted.append("personal_paths")
        out = out2
    # Emails
    out2 = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "***@***.***", out)
    if out2 != out:
        redacted.append("emails")
        out = out2
    return out, list(sorted(set(redacted)))


def build_ceo(user_text: str, session_id: Optional[str] = None, timestamp: Optional[str] = None) -> Dict[str, Any]:
    # Query local memory directly to avoid network loop
    related = memory_agent.search_memories(user_text or "", limit=10)
    context_additions = []
    for r in related[:5]:
        context_additions.append(f"[{r.get('id')}] {r.get('summary') or r.get('goal')}")
    context_text = "\n".join(context_additions)
    # Summarize context by conversation/session id if provided
    memory_summary = None
    if session_id:
        try:
            memory_summary = memory_agent.generate_context_summary(session_id)  # type: ignore[arg-type]
        except Exception:
            memory_summary = None
    redacted_text, private_fields = _redact_private(user_text or "")
    model = os.getenv("JOJO_BRIDGE_MODEL", os.getenv("AI_FACTORY_CLOUD_MODEL", "gpt-4o"))
    return {
        "user_text": user_text or "",
        "sanitized_text": redacted_text,
        "context_additions": context_text,
        "memory_summary": memory_summary or "",
        "private_fields_redacted": private_fields,
        "target_model": model or "gpt-4o",
        "session_id": session_id,
        "timestamp": timestamp or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def handle_chat(user_text: str, session_id: Optional[str] = None, timestamp: Optional[str] = None) -> Dict[str, Any]:
    ceo = build_ceo(user_text=user_text, session_id=session_id, timestamp=timestamp)
    # Forward to proxy
    proxy_result = call_chatgpt(ceo)
    # Integrate back (memory updates, summary)
    integrated = integrate_response(ceo, proxy_result)
    # Audit log
    try:
        Path("logs").mkdir(exist_ok=True)
        with open("logs/bridge.log", "a", encoding="utf-8") as f:
            f.write(f"CHAT ceo.session={ceo.get('session_id')} ok\n")
    except Exception:
        pass
    return integrated


def bridge_status() -> Dict[str, Any]:
    # Health of model + memory
    try:
        from ai_factory.memory.memory_agent import stats as mem_stats
        mstats = mem_stats()
    except Exception:
        mstats = {"total": None}
    mode = os.getenv("JOJO_BRIDGE_MODE", "exact_relay")
    model = os.getenv("JOJO_BRIDGE_MODEL", os.getenv("AI_FACTORY_CLOUD_MODEL", "gpt-4o"))
    return {"bridge": "ok", "mode": mode, "model": model, "memory": mstats}

