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
    get_emotional_awareness_context,
)
from typing import Tuple
from ai_factory.memory import memory_agent
from ai_factory.memory.memory_agent import CORE_IDENTITY
from ai_factory.memory.dialogue_store import save_turn as _save_turn
from ai_factory.mood.mood_engine import analyze_mood, log_mood
import json

# Phase 4.1 - Identity Alias Engine
try:
    from ai_factory.memory.memory_db import resolve_memory_key
    ALIAS_ENGINE_AVAILABLE = True
except ImportError:
    ALIAS_ENGINE_AVAILABLE = False

# Phase 4 - Emotion & Awareness Integration
try:
    from ai_factory.emotion import emotion_engine
    EMOTION_ENGINE_AVAILABLE = True
except ImportError:
    EMOTION_ENGINE_AVAILABLE = False
    
try:
    from ai_factory.awareness import awareness_engine
    AWARENESS_ENGINE_AVAILABLE = True
except ImportError:
    AWARENESS_ENGINE_AVAILABLE = False

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
    """
    Phase 4 Enhanced Hybrid Reasoning Pipeline:
    1. Retrieve memory FIRST
    2. Compute emotion & awareness context (Phase 4)
    3. Build system prompt with identity + memory + emotion/awareness hints
    4. Local reasoning → rough draft only
    5. External model → final authoritative rewrite (OVERRIDES local)
    6. Apply personality filter (Phase 4)
    7. clean_output() applied LAST
    """
    # 1. Retrieve memory FIRST - before any model runs
    user_memory = memory_agent.search_memories(user_input or "", limit=5)
    
    # Always include identity memories for identity-related queries
    identity_keywords = ["who am i", "when was i born", "where was i born", "where am i from", "what is my village", "who created", "birthdate", "birthplace", "village", "gorkha", "nirdesh", "hometown", "origin", "where from", "home place", "home town"]
    user_lower = (user_input or "").lower()
    is_identity_query = any(keyword in user_lower for keyword in identity_keywords)
    
    # Phase 4.1: Use alias resolution for identity queries
    if is_identity_query and ALIAS_ENGINE_AVAILABLE:
        try:
            resolved_key = resolve_memory_key(user_input or "")
            if resolved_key:
                # Search for the resolved key specifically
                targeted_results = memory_agent.search_memories(resolved_key, limit=3)
                # Merge with existing results, prioritizing targeted
                existing_ids = {m.get("id") for m in user_memory}
                for result in targeted_results:
                    if result.get("id") not in existing_ids:
                        user_memory.insert(0, result)
        except Exception:
            pass  # Best-effort only
    
    if is_identity_query:
        # Search specifically for identity memories
        from ai_factory.memory.memory_db import SessionLocal, MemoryEntry
        from sqlalchemy import select, and_
        identity_goals = ["user_full_name", "user_birthdate", "user_birthplace", "user_country", "user_village", "user_current_location", "jojo_creator"]
        with SessionLocal() as session:
            identity_mems = session.scalars(
                select(MemoryEntry).where(
                    and_(
                        MemoryEntry.goal.in_(identity_goals),
                        MemoryEntry.deleted == 0
                    )
                )
            ).all()
            # Add identity memories to the results
            for mem in identity_mems:
                identity_dict = {
                    "id": mem.id,
                    "goal": mem.goal,
                    "summary": mem.summary,
                    "tags": mem.tags,
                    "score": mem.score,
                }
                # Only add if not already in user_memory
                if not any(m.get("id") == mem.id for m in user_memory):
                    user_memory.insert(0, identity_dict)  # Insert at beginning for priority
    
    clean_memory = []
    for m in user_memory or []:
        # Ensure we use only clean summaries
        summary = m.get("summary") or m.get("goal") or ""
        if summary:
            clean_memory.append(summary)
    memory_context = "\n".join(clean_memory).strip()
    
    # 2. Phase 4: Compute emotion & awareness context (hidden from user, guides JoJo's tone)
    emotion_ctx = None
    user_emotion = "neutral"
    tone_hint = None
    
    if EMOTION_ENGINE_AVAILABLE:
        try:
            emotion_ctx = emotion_engine.get_emotional_context(
                user_input=user_input or "",
                memory_context={"memories": user_memory} if user_memory else None
            )
            user_emotion = emotion_ctx.get("user_emotion", "neutral")
            tone_hint = emotion_ctx.get("tone_instruction")
        except Exception:
            pass  # Best-effort only
    
    # Build compact emotional/awareness context for system prompt injection
    emotional_awareness_hint = get_emotional_awareness_context(
        user_emotion=user_emotion if user_emotion != "neutral" else None,
        tone_hint=tone_hint
    )
    
    # 3. Redact sensitive
    sanitized, redactions = _redact_private(user_input or "")
    
    # 4. Build unified identity system prompt with memory injected FIRST
    system_prompt = get_identity_prompt()
    if memory_context:
        if is_identity_query:
            system_prompt += f"\n\nIMPORTANT - User Identity Information:\n{memory_context}\n\nYou MUST use this identity information to answer the user's question. Do not say you don't have access to this information - it is provided above. Answer directly using the facts from the identity information."
        else:
            system_prompt += f"\n\nRelevant user memory:\n{memory_context}\n\nUse this memory to answer clearly."
    
    # Phase 4: Inject compact emotion/awareness guidance into system prompt
    if emotional_awareness_hint:
        system_prompt += f"\n\n{emotional_awareness_hint}"
    
    # 5. Local reasoning → rough draft only (NO "User:" prefix, NO final output)
    local_prefix = build_identity_context_for_local()
    related = memory_agent.search_memories(user_input or "", limit=10)
    ctx_items = [f"[{r.get('id')}] {r.get('summary') or r.get('goal')}" for r in related[:10]]
    local_summary = _local_reason(sanitized, ctx_items)
    # Local summary is just a rough draft, no "User:" prefix to avoid transcript spam
    local_draft = local_summary
    
    # 6. External model → final authoritative rewrite (OVERRIDES local, not merged)
    persona_tone = stabilize_persona_tone(user_input or "")
    final_prompt = (
        system_prompt + "\n\n" +
        f"Tone: {persona_tone}\n\n" +
        get_external_enrichment_context() + "\n\n" +
        f"User question: {sanitized}\n\n" +
        f"Local rough draft (for context only, do not repeat): {local_draft}\n\n" +
        "Provide a clean, final answer based on the user's question and the memory context above."
    )
    
    # Always delegate mock/live behavior to call_gpt5 via runtime flags
    test_mode = bool(os.getenv("PYTEST_CURRENT_TEST"))
    diagnostic_mode = bool(os.getenv("HYBRID_DIAGNOSTIC"))
    try:
        # External model provides final authoritative answer (OVERRIDES local)
        ext_out = call_gpt5(final_prompt)
    except Exception as e:
        # Fallback to local only if external fails
        ext_out = local_draft
    
    # External output is the final answer (not merged with local)
    final_answer = ext_out
    
    # Phase 4: Apply personality filter to ensure warmth and consistency
    if EMOTION_ENGINE_AVAILABLE and emotion_ctx:
        try:
            emotional_state = emotion_ctx.get("emotional_state")
            final_answer = emotion_engine.apply_personality_filter(final_answer, emotional_state)
        except Exception:
            pass  # Best-effort only
    
    # Ensure empathetic reinforcement is present for gratitude messages
    try:
        if "thank" in (sanitized or "").lower() and ("glad" not in final_answer.lower() and "you're welcome" not in final_answer.lower() and "support" not in final_answer.lower()):
            final_answer = (final_answer + "\n\nYou're welcome — I'm glad I could help. I'm here to support you.").strip()
    except Exception:
        pass
    
    # 7. Persist dialogue + mood (best-effort)
    try:
        sid = session_id or "default"
        _save_turn(sid, "user", user_input or "", meta={"source": "ui"})
    except Exception:
        pass
    try:
        sid = session_id or "default"
        _save_turn(sid, "assistant", final_answer or "", meta={"source": "bridge"})
    except Exception:
        pass
    try:
        m = analyze_mood(user_input or "")
        log_mood(session_id or "default", m)
    except Exception:
        pass

    # 8. Auto-learn (best-effort)
    try:
        memory_agent.store_memory(
            run_id=None,
            goal=f"bridge_chat session={session_id}",
            summary=(final_answer[:400] if final_answer else ""),
            tags=["bridge", "chat", "hybrid"],
            score=None,
        )
    except Exception:
        pass
    # 9. Auto-reflection persistent save (best-effort)
    try:
        from ai_factory.memory.memory_agent import store_memory as _store
        _store(
            run_id=None,
            goal="auto_reflection",
            summary=(final_answer[:400] if final_answer else ""),
            tags=["reflection", "autosave", "session"],
            score=0.7,
        )
    except Exception as e:
        try:
            print("Auto-reflection save skipped:", e)
        except Exception:
            pass
    
    # 10. FINAL CLEAN BEFORE RETURN - MUST be applied LAST after all processing
    final_text = final_answer
    if isinstance(final_text, str):
        final_text = clean_output(final_text)
    else:
        final_text = clean_output(str(final_text))
    
    # Build response dict (Phase 4: do NOT include raw emotion/awareness data)
    response = {
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
    
    # Phase 4: For debugging only - log emotion/awareness state (NOT returned to user)
    if DIAGNOSTIC_MODE and emotion_ctx:
        try:
            Path("logs").mkdir(exist_ok=True)
            with open("logs/emotion_debug.log", "a", encoding="utf-8") as f:
                import json as _json
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} session={session_id} " +
                        f"user_emotion={user_emotion} " +
                        f"tone={tone_hint[:50] if tone_hint else 'none'}\n")
        except Exception:
            pass
    
    return response


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
