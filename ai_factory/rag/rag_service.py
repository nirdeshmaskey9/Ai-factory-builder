from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Tuple

from sentence_transformers import SentenceTransformer  # type: ignore
import numpy as np
import time

from .vector_db import build_or_load_index, persist, search
from .doc_loader import load_document
from ai_factory.memory.memory_mcp import get_recent_memories, load_feedback_log


_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_EMB = None
_LAST_SYNC_FILE = Path("data/vector_db/last_sync.txt")


def _emb_model():
    global _EMB
    if _EMB is None:
        _EMB = SentenceTransformer(_MODEL_NAME)
    return _EMB


def embed_text(text: str, model: str | None = None):
    m = _emb_model() if not model else SentenceTransformer(model)
    v = m.encode([text], normalize_embeddings=True)
    return v[0]


def _chunk_hash(text: str) -> str:
    import hashlib
    return hashlib.sha1((text or "").encode("utf-8", errors="ignore")).hexdigest()


def ingest_document(path: str, tags: List[str] | None = None) -> Dict:
    docs = load_document(path)
    m = _emb_model()
    index, store_docs, store_meta, files = build_or_load_index(m)

    new_vecs: List[np.ndarray] = []
    for d in docs:
        txt = d.get("page_content") or ""
        meta = dict(d.get("metadata") or {})
        if tags:
            meta["tags"] = list(tags)
        # ensure stable hash/id for feedback mapping
        h = _chunk_hash(txt)
        meta.setdefault("hash", h)
        vec = m.encode([txt], normalize_embeddings=True)[0]
        new_vecs.append(vec)
        store_docs.append(txt)
        store_meta.append(meta)

    if new_vecs:
        import faiss  # type: ignore
        arr = np.vstack(new_vecs)
        index.add(arr)
    persist(index, files, store_docs, store_meta)

    return {"chunks": len(docs)}


def retrieve(query: str, top_k: int = 5) -> List[Dict]:
    m = _emb_model()
    index, docs, meta, _ = build_or_load_index(m)
    if not docs:
        return []
    qv = m.encode([query], normalize_embeddings=True)[0]
    idxs, scores = search(index, qv, top_k=top_k)
    out: List[Dict] = []
    for i, s in zip(idxs, scores):
        if 0 <= i < len(docs):
            m_i = meta[i] if i < len(meta) else {}
            txt = docs[i]
            h = m_i.get("hash") or _chunk_hash(txt)
            o = {
                "text": txt,
                "score": float(s),
                "metadata": {**m_i, "hash": h},
            }
            out.append(o)
    # feedback weighting
    try:
        fb = load_feedback_log()  # {hash: {rating,...}}
        def weight(sc: float, chash: str) -> float:
            r = int((fb.get(chash) or {}).get("rating") or 0)
            return float(sc) * (1.0 + (0.05 * max(0, r)))
        for r in out:
            ch = r.get("metadata", {}).get("hash") or ""
            r["score"] = weight(float(r.get("score") or 0.0), ch)
        out.sort(key=lambda x: float(x.get("score") or 0.0), reverse=True)
    except Exception:
        pass
    return out


def retrieve_with_retry(query: str, top_k: int = 5, min_score: float = 0.40, retry: bool = True) -> List[Dict]:
    res = retrieve(query, top_k=top_k)
    if not retry:
        return res
    best = max((float(r.get("score") or 0.0) for r in res), default=0.0)
    if best < float(min_score):
        return retrieve(query, top_k=top_k + 3)
    return res


def sync_with_memory_mcp(limit: int = 200) -> Dict:
    """Pull recent memory summaries, embed with SAME model, upsert to FAISS.

    Returns: {"added": int, "skipped": int, "total": int, "last_sync": float}
    """
    m = _emb_model()
    index, store_docs, store_meta, files = build_or_load_index(m)
    existing = set()
    for m_i in (store_meta or []):
        try:
            existing.add(str(m_i.get("hash") or ""))
        except Exception:
            continue
    memories = []
    try:
        memories = get_recent_memories(limit=limit)
    except Exception:
        memories = []
    new_vecs: List[np.ndarray] = []
    added = 0
    skipped = 0
    for mem in memories:
        txt = str(mem.get("text") or "").strip()
        if not txt:
            continue
        h = _chunk_hash(txt)
        if h in existing:
            skipped += 1
            continue
        vec = m.encode([txt], normalize_embeddings=True)[0]
        new_vecs.append(vec)
        store_docs.append(txt)
        mm = {"hash": h, "type": "memory", "tags": list(mem.get("tags") or [])}
        store_meta.append(mm)
        existing.add(h)
        added += 1
    if new_vecs:
        import faiss  # type: ignore
        arr = np.vstack(new_vecs)
        index.add(arr)
        persist(index, files, store_docs, store_meta)
    ts = time.time()
    try:
        _LAST_SYNC_FILE.parent.mkdir(parents=True, exist_ok=True)
        _LAST_SYNC_FILE.write_text(str(ts), encoding="utf-8")
    except Exception:
        pass
    return {"added": added, "skipped": skipped, "total": len(store_docs), "last_sync": ts}
