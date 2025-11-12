from __future__ import annotations

from typing import Dict, Any, List
from pathlib import Path
import json, time


FEEDBACK_PATH = Path("data/memory/feedback_log.json")
MEMORY_DIR = Path("data/memory")


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
        "ts": time.time(),
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


def get_recent_memories(limit: int = 200) -> List[Dict[str, Any]]:
    """Read recent summarized memories from data/memory.

    Supports optional files:
    - data/memory/summaries.json (list of objects)
    - data/memory/*.jsonl (each line is a JSON object)
    Returns list of {id, text, ts, tags} sorted by ts desc (best-effort).
    """
    out: List[Dict[str, Any]] = []
    try:
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        summ = MEMORY_DIR / "summaries.json"
        if summ.exists():
            try:
                data = json.loads(summ.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    for it in data:
                        if not isinstance(it, dict):
                            continue
                        out.append({
                            "id": str(it.get("id") or it.get("rid") or ""),
                            "text": str(it.get("summary") or it.get("text") or ""),
                            "ts": float(it.get("ts") or time.time()),
                            "tags": list(it.get("tags") or []),
                        })
            except Exception:
                pass
        # Fallback: scan for .jsonl files
        if len(out) < limit:
            for p in sorted(MEMORY_DIR.glob("*.jsonl"), key=lambda x: x.stat().st_mtime, reverse=True):
                try:
                    for line in p.read_text(encoding="utf-8").splitlines():
                        try:
                            it = json.loads(line)
                        except Exception:
                            continue
                        out.append({
                            "id": str(it.get("id") or it.get("rid") or ""),
                            "text": str(it.get("summary") or it.get("text") or ""),
                            "ts": float(it.get("ts") or time.time()),
                            "tags": list(it.get("tags") or []),
                        })
                        if len(out) >= limit:
                            break
                except Exception:
                    continue
                if len(out) >= limit:
                    break
    except Exception:
        return out[:limit]
    # Sort by ts desc and cap
    try:
        out.sort(key=lambda x: x.get("ts", 0.0), reverse=True)
    except Exception:
        pass
    return out[:limit]


def load_feedback_log() -> Dict[str, Dict[str, Any]]:
    """Return mapping of {chunk_hash: {rating, notes, ts}} from feedback_log.json.

    If entries lack "context.chunk_hash", they are ignored for weighting.
    """
    _ensure_feedback_dir()
    try:
        data = json.loads(FEEDBACK_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            return {}
    except Exception:
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    for it in data:
        try:
            ctx = it.get("context") or {}
            ch = str(ctx.get("chunk_hash") or "").strip()
            if not ch:
                continue
            out[ch] = {
                "rating": int(it.get("rating") or 0),
                "notes": str(it.get("notes") or ""),
                "ts": float(it.get("ts") or 0.0),
            }
        except Exception:
            continue
    return out
