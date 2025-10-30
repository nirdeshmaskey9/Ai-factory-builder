from __future__ import annotations

from typing import Dict, Any, List
from pathlib import Path

from ai_factory.memory import memory_agent


def _infer_memory_updates(text: str) -> List[Dict[str, str]]:
    # Very lightweight inference: extract lines that look like preferences/facts
    updates: List[Dict[str, str]] = []
    if not text:
        return updates
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for l in lines:
        if l.lower().startswith(("pref:", "preference:", "fact:", "remember:")):
            updates.append({"type": "note", "content": l})
    return updates


def integrate_response(ceo: Dict[str, Any], proxy_result: Dict[str, Any]) -> Dict[str, Any]:
    text = proxy_result.get("response_text") or ""
    updates = _infer_memory_updates(text)
    # Store a summarized memory record (structured only)
    try:
        goal = f"bridge_chat session={ceo.get('session_id')}"
        summary = text[:400]
        tags = ["bridge", "chat", str(ceo.get("target_model") or "")]
        memory_agent.store_memory(run_id=None, goal=goal, summary=summary, tags=tags, score=None)
    except Exception:
        pass
    # Optional conversation summary regeneration
    summary_text = ""
    try:
        if ceo.get("session_id"):
            summary_text = memory_agent.generate_context_summary(ceo.get("session_id"))  # type: ignore[arg-type]
    except Exception:
        summary_text = ""
    # Log minimal info
    try:
        Path("logs").mkdir(exist_ok=True)
        with open("logs/bridge.log", "a", encoding="utf-8") as f:
            f.write("INTEGRATED ok\n")
    except Exception:
        pass
    return {
        "response_text": text,
        "model": proxy_result.get("model"),
        "memory_updates": updates,
        "summary": summary_text,
        "ceo": {  # include for debugging/validation
            "user_text": ceo.get("user_text"),
            "sanitized_text": ceo.get("sanitized_text"),
            "private_fields_redacted": ceo.get("private_fields_redacted"),
            "context_additions": ceo.get("context_additions"),
        },
    }

