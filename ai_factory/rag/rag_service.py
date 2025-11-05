from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Tuple

from sentence_transformers import SentenceTransformer  # type: ignore
import numpy as np

from .vector_db import build_or_load_index, persist, search
from .doc_loader import load_document


_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_EMB = None


def _emb_model():
    global _EMB
    if _EMB is None:
        _EMB = SentenceTransformer(_MODEL_NAME)
    return _EMB


def embed_text(text: str, model: str | None = None):
    m = _emb_model() if not model else SentenceTransformer(model)
    v = m.encode([text], normalize_embeddings=True)
    return v[0]


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
            out.append({
                "text": docs[i],
                "score": float(s),
                "metadata": meta[i] if i < len(meta) else {},
            })
    return out


def sync_with_memory_mcp() -> int:
    """No-op stub for now; placeholder for syncing summarized memory to RAG.

    Returns number of items synced.
    """
    # Future: read ai_factory.memory.memory_store/memory_db and embed summaries
    return 0

