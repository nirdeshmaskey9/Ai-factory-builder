from __future__ import annotations

"""
Nightly self-evaluation script for RAG precision@k.

Re-runs recent queries from data/memory/query_log.json (if present),
optionally using feedback notes' keywords for expected matches, and
writes metrics to data/memory/metrics.json. Best-effort; never crashes.
"""

import json
import time
from pathlib import Path
from typing import List, Dict


QUERY_LOG = Path("data/memory/query_log.json")
METRICS = Path("data/memory/metrics.json")


def _load_queries(limit: int = 50) -> List[Dict]:
    if not QUERY_LOG.exists():
        return []
    try:
        data = json.loads(QUERY_LOG.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data[-limit:]
    except Exception:
        return []
    return []


def _keywords_from_feedback(notes: str) -> List[str]:
    try:
        txt = (notes or "").lower()
        # naive split on spaces; filter short tokens
        return [t for t in txt.replace("\n", " ").split(" ") if len(t) > 3][:5]
    except Exception:
        return []


def _precision_at_k(results: List[Dict], keywords: List[str], k: int = 5) -> float:
    if not results or not keywords:
        return 0.0
    top = results[:k]
    hits = 0
    for r in top:
        t = (r.get("text") or "").lower()
        if any(kw in t for kw in keywords):
            hits += 1
    return hits / max(1, min(k, len(results)))


def run(limit: int = 50) -> Dict:
    try:
        from ai_factory.rag.rag_service import retrieve_with_retry
        from ai_factory.memory.memory_mcp import load_feedback_log
    except Exception:
        return {"error": "dependencies not available"}
    queries = _load_queries(limit)
    fb = load_feedback_log()
    rows = []
    for q in queries:
        qtext = str(q.get("query") or "")
        if not qtext:
            continue
        exp_notes = str(q.get("notes") or "")
        kws = _keywords_from_feedback(exp_notes)
        try:
            res = retrieve_with_retry(qtext, top_k=5, min_score=0.4, retry=True)
            p5 = _precision_at_k(res, kws, k=5) if kws else 0.0
        except Exception:
            p5 = 0.0
        rows.append({"query": qtext, "p@5": p5})
    avg = sum(r.get("p@5", 0.0) for r in rows) / max(1, len(rows))
    out = {"ts": time.time(), "n": len(rows), "avg_p@5": avg, "rows": rows}
    try:
        METRICS.parent.mkdir(parents=True, exist_ok=True)
        METRICS.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass
    return out


if __name__ == "__main__":
    res = run(limit=50)
    print(json.dumps(res, ensure_ascii=False))

