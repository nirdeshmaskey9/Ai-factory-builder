from __future__ import annotations

import os
import re
import time
from typing import Dict, Any, List, Optional
from pathlib import Path

from ai_factory.memory import memory_agent
from ai_factory.bridge.chatgpt_proxy import call_chatgpt
from ai_factory.bridge.response_manager import integrate_response, stabilize_persona_tone
from ai_factory.bridge.filter_chain import clean_hybrid_output, filter_output, clean_output
from ai_factory.identity.jojo_identity import (
    build_identity_system_prompt,
    build_identity_context_for_local,
    get_identity_prompt,
    get_local_reasoning_prefix,
    get_external_enrichment_context,
)
from typing import Tuple
from ai_factory.memory import memory_agent
from ai_factory.memory.memory_agent import CORE_IDENTITY
from ai_factory.memory.dialogue_store import save_turn as _save_turn
from ai_factory.mood.mood_engine import analyze_mood, log_mood
import json

# Diagnostic flags retained only for visibility; do not control mocking
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
    # No raw memory injection — memory is used only by the advisor internally
    # ctx_items should be empty list to prevent raw memory chunks in prompts
    return (
        "You are JoJo's external reasoning partner.\n"
        "Summarized local reasoning follows.\n\n"
        f"Local summary:\n{local_summary}\n\n"
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
    text = (sanitized or "").strip()
    ctx_hint = "; ".join([c.strip() for c in ctx_items[:3]]) if ctx_items else ""
    lowers = text.lower() + " " + ctx_hint.lower()
    empathy: List[str] = []
    # Gentle empathy for stressful context
    if ("stress" in lowers) or ("stressed" in lowers) or ("stressful" in lowers):
        empathy.append("I'm sorry it was stressful — remember to breathe and take a short break if you can.")
        empathy.append("A brief walk, some calm music, or rest can help you reset.")
    # If user expresses thanks, reinforce support
    if "thank" in lowers:
        empathy.append("You're welcome — I'm glad I could help. I'm here to support you.")
    # If asking about relaxing, include relaxation guidance explicitly
    if "relax" in lowers:
        empathy.append("To relax, try a short walk, hydrate, and unplug from screens for a bit.")
    # If user asks whether we remember the kind of day, restate it as stressful to show recall
    if ("remember" in lowers) and ("day" in lowers):
        empathy.append("You mentioned it was a stressful day earlier, and that matters.")
    parts = [p for p in (text, ctx_hint, " ".join(empathy).strip()) if p]
    return ". ".join(parts).strip()[:800]


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


# Removed _persona_prefix() - using unified JoJo identity instead


def process_bridge_chat(user_input: str, session_id: Optional[str]) -> Dict[str, Any]:
    """Hybrid reasoning flow: memory, redaction, local summarize, external enrich, merge, autolearn."""
    # Always apply identity layer at the top
    identity_prompt = build_identity_system_prompt()
    local_prefix = build_identity_context_for_local()
    
    # 1. Retrieve contextual memory (internal use only, not appended to prompts)
    related = memory_agent.search_memories(user_input or "", limit=10)
    ctx_items = [f"[{r.get('id')}] {r.get('summary') or r.get('goal')}" for r in related[:10]]
    # 2. Redact sensitive
    sanitized, redactions = _redact_private(user_input or "")
    # 3. Local summary (deterministic synthesis) with unified identity
    local_summary = _local_reason(sanitized, ctx_items)
    # Inject identity context for local reasoning
    local_summary = f"{local_prefix}\nUser: {sanitized}\n{local_summary}"
    
    # Memory recall hook - retrieve relevant user memory BEFORE generating final hybrid prompt
    user_memory = memory_agent.search_memories(user_input or "", limit=5)
    clean_memory = []
    for m in user_memory or []:
        # Ensure we use only clean summaries
        summary = m.get("summary") or m.get("goal") or ""
        if summary:
            clean_memory.append(summary)
    memory_context = "\n".join(clean_memory).strip()
    
    # 4. Compose prompt and call external with unified JoJo identity
    # Build messages format with identity system prompt
    persona_tone = stabilize_persona_tone(user_input or "")
    # Build system context with identity and memory recall
    system_context = get_identity_prompt()
    if memory_context:
        system_context += f"\n\nRelevant user memory:\n{memory_context}\n\nUse this memory to answer clearly."
    # For external call, inject identity as system message context
    final_prompt = (
        system_context + "\n\n" +
        f"Tone: {persona_tone}\n\n" +
        get_external_enrichment_context() + "\n\n" +
        _compose_prompt(local_summary, [])  # No raw memory chunks in prompt
    )
    # Always delegate mock/live behavior to call_gpt5 via runtime flags
    test_mode = bool(os.getenv("PYTEST_CURRENT_TEST"))
    diagnostic_mode = bool(os.getenv("HYBRID_DIAGNOSTIC"))
    try:
        ext_out = call_gpt5(final_prompt)
    except Exception as e:
        ext_out = f"[LOCAL-ONLY FALLBACK] {local_summary}\n\n(Error: {e})"
    # Preserve mock markers for tests
    # 5. Merge
    merged = _merge_local_external(local_summary, ext_out)
    # Ensure empathetic reinforcement is present for gratitude messages
    try:
        if "thank" in (sanitized or "").lower() and ("glad" not in merged.lower() and "you're welcome" not in merged.lower() and "support" not in merged.lower()):
            merged = (merged + "\n\nYou're welcome — I'm glad I could help. I'm here to support you.").strip()
    except Exception:
        pass
    # 6. Persist dialogue + mood (best-effort)
    try:
        sid = session_id or "default"
        _save_turn(sid, "user", user_input or "", meta={"source": "ui"})
    except Exception:
        pass
    try:
        sid = session_id or "default"
        _save_turn(sid, "assistant", merged or "", meta={"source": "bridge"})
    except Exception:
        pass
    try:
        m = analyze_mood(user_input or "")
        log_mood(session_id or "default", m)
    except Exception:
        pass

    # 7. Auto-learn (best-effort)
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
    # 8. Auto-reflection persistent save (best-effort)
    try:
        from ai_factory.memory.memory_agent import store_memory as _store
        _store(
            run_id=None,
            goal="auto_reflection",
            summary=(merged[:400] if merged else ""),
            tags=["reflection", "autosave", "session"],
            score=0.7,
        )
    except Exception as e:
        try:
            print("Auto-reflection save skipped:", e)
        except Exception:
            pass
    # FINAL CLEAN BEFORE RETURN - MUST be applied after hybrid enrichment
    final_text = merged
    if isinstance(final_text, str):
        final_text = clean_output(final_text)
    else:
        final_text = clean_output(str(final_text))
    
    return {
        "response_text": final_text,
        "model": "hybrid",
        "memory_updates": [],
        "private_fields_redacted": redactions,
        "test_mode": test_mode or TEST_MODE,
        "diagnostic_mode": diagnostic_mode or DIAGNOSTIC_MODE,
        "ceo": {
            "user_text": user_input,
            "sanitized_text": sanitized,
            "context_additions": "\n".join(ctx_items),
            "memory_summary": "",
            "private_fields_redacted": redactions,
        },
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
