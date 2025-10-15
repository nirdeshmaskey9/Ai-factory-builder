from __future__ import annotations

from fastapi import APIRouter, Query
from ai_factory.memory.memory_store import get_recent, create_snapshot
from ai_factory.memory.memory_embeddings import semantic_search

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/logs")
def read_logs(limit: int = Query(10, ge=1, le=500)):
    events = get_recent(limit)
    return [
        {
            "id": e.id,
            "request_id": e.request_id,
            "task_type": e.task_type,
            "prompt": e.prompt,
            "timestamp": e.timestamp.isoformat(),
        }
        for e in events
    ]


@router.get("/search")
def search_memory(q: str = Query(..., min_length=1), n: int = Query(3, ge=1, le=20)):
    results = semantic_search(q, n_results=n)
    # Normalize into a friendly shape
    hits = []
    ids = results.get("ids", [[]])[0] if results else []
    docs = results.get("documents", [[]])[0] if results else []
    dists = results.get("distances", [[]])[0] if results else []
    for i, doc_id in enumerate(ids):
        hits.append({"id": doc_id, "text": docs[i] if i < len(docs) else None, "distance": dists[i] if i < len(dists) else None})
    return {"query": q, "results": hits}


@router.get("/snapshot")
def snapshot(limit: int = Query(100, ge=1, le=2000)):
    path = create_snapshot(limit=limit)
    return {"status": "ok", "snapshot": path}

