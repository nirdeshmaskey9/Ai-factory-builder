from __future__ import annotations

import os
import re
import time
from typing import Dict, Any, List, Optional
from pathlib import Path

from ai_factory.memory import memory_agent
from ai_factory.bridge.chatgpt_proxy import call_chatgpt
from ai_factory.bridge.response_manager import integrate_response
from typing import Tuple

# Diagnostic flags (evaluated at import; functions also re-read dynamically)
TEST_MODE = bool(os.getenv("PYTEST_CURRENT_TEST"))
DIAGNOSTIC_MODE = bool(os.getenv("HYBRID_DIAGNOSTIC"))


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


# --- Hybrid Reasoning Helpers (v3.3-hybrid) ---
def _compose_prompt(local_summary: str, ctx_items: List[str]) -> str:
    ctx_block = "\n".join(ctx_items[:10]) if ctx_items else ""
    return (
        "You are JoJo's external reasoning partner.\n"
        "Summarized local reasoning follows, along with contextual memory.\n\n"
        f"Local summary:\n{local_summary}\n\n"
        f"Context:\n{ctx_block}\n"
    )


def _merge_local_external(local_summary: str, external_text: str) -> str:
    if not external_text:
        return local_summary
    return f"[Local]\n{local_summary}\n\n[External]\n{external_text}".strip()


def call_gpt5(prompt: str) -> str:
    """Thin wrapper to allow monkeypatch in tests. Falls back to chatgpt proxy."""
    try:
        # Reuse existing proxy; pack into ceo-like payload
        resp = call_chatgpt({"sanitized_text": prompt, "user_text": prompt, "context_additions": "", "memory_summary": "", "target_model": "gpt-5"})
        return str(resp.get("response_text") or "")
    except Exception:
        return ""


def _local_reason(sanitized: str, ctx_items: List[str]) -> str:
    # Deterministic lightweight local reasoning summary (no LLM dependency here)
    h = (sanitized or "").strip()
    ctx_hint = "; ".join([c.strip() for c in ctx_items[:3]]) if ctx_items else ""
    parts = [p for p in (h, ctx_hint) if p]
    return ". ".join(parts)[:800]


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
    # Back-compat exact relay path
    ceo = build_ceo(user_text=user_text, session_id=session_id, timestamp=timestamp)
    proxy_result = call_chatgpt(ceo)
    integrated = integrate_response(ceo, proxy_result)
    try:
        Path("logs").mkdir(exist_ok=True)
        with open("logs/bridge.log", "a", encoding="utf-8") as f:
            f.write(f"CHAT ceo.session={ceo.get('session_id')} ok\n")
    except Exception:
        pass
    return integrated


def process_bridge_chat(user_input: str, session_id: Optional[str]) -> Dict[str, Any]:
    """Hybrid reasoning flow: memory, redaction, local summarize, external enrich, merge, autolearn."""
    # 1. Retrieve contextual memory
    related = memory_agent.search_memories(user_input or "", limit=10)
    ctx_items = [f"[{r.get('id')}] {r.get('summary') or r.get('goal')}" for r in related[:10]]
    # 2. Redact sensitive
    sanitized, redactions = _redact_private(user_input or "")
    # 3. Local summary (deterministic synthesis)
    local_summary = _local_reason(sanitized, ctx_items)
    # 4. Compose prompt and call external
    final_prompt = _compose_prompt(local_summary, ctx_items)
    # Dynamic diagnostic flags re-check for each call to honor test environment changes
    test_mode = bool(os.getenv("PYTEST_CURRENT_TEST"))
    diagnostic_mode = bool(os.getenv("HYBRID_DIAGNOSTIC"))
    if test_mode and not diagnostic_mode:
        ext_out = "[MOCK GPT-5 RESPONSE: Test Mode]"
    else:
        try:
            ext_out = call_gpt5(final_prompt)
        except Exception as e:
            ext_out = f"[LOCAL-ONLY FALLBACK] {local_summary}\n\n(Error: {e})"
    # 5. Merge
    merged = _merge_local_external(local_summary, ext_out)
    # 6. Auto-learn (best-effort)
    try:
        memory_agent.store_memory(
            run_id=None,
            goal=f"bridge_chat session={session_id}",
            summary=(merged[:400] if merged else ""),
            tags=["bridge", "chat", "hybrid"],
            score=None,
        )
    except Exception:
        pass
    return {
        "response_text": merged,
        "model": "hybrid",
        "memory_updates": [],
        "private_fields_redacted": redactions,
        "test_mode": test_mode or TEST_MODE,
        "diagnostic_mode": diagnostic_mode or DIAGNOSTIC_MODE,
    }


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
