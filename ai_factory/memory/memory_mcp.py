from __future__ import annotations

from typing import Dict, Any, List
from pathlib import Path
import json


FEEDBACK_PATH = Path("data/memory/feedback_log.json")


def _ensure_feedback_dir() -> None:
    FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not FEEDBACK_PATH.exists():
        FEEDBACK_PATH.write_text("[]", encoding="utf-8")


def record_feedback(event: str, rating: int, notes: str, context: Dict[str, Any] | None = None) -> None:
    """Append a feedback entry to feedback_log.json.

    rating: int in range 1..5
    """
    _ensure_feedback_dir()
    try:
        rating_i = int(rating)
    except Exception:
        rating_i = 0
    entry = {
        "event": str(event or ""),
        "rating": rating_i,
        "notes": str(notes or ""),
        "context": context or {},
    }
    try:
        cur = json.loads(FEEDBACK_PATH.read_text(encoding="utf-8"))
        if not isinstance(cur, list):
            cur = []
    except Exception:
        cur = []
    cur.append(entry)
    FEEDBACK_PATH.write_text(json.dumps(cur, ensure_ascii=False, indent=2), encoding="utf-8")


def integrate_rag_context(rag_results: List[Dict[str, Any]]) -> int:
    """Merge retrieved RAG snippets with short-term memory store.

    Returns number of items merged.
    """
    try:
        from ai_factory.memory.memory_agent import store_memory
    except Exception:
        return 0
    n = 0
    try:
        for r in rag_results or []:
            txt = str(r.get("text") or r.get("page_content") or "")
            if not txt:
                continue
            meta = r.get("metadata") or {}
            tags = ["rag_merge"] + list(meta.get("tags") or [])
            store_memory(None, goal="RAG merge", summary=txt[:1000], tags=tags, score=None)
            n += 1
    except Exception:
        return n
    return n

