from __future__ import annotations

from fastapi import APIRouter, Query, HTTPException
from ai_factory.memory.memory_store import get_recent, create_snapshot
from ai_factory.memory.memory_embeddings import semantic_search
from ai_factory.memory.memory_agent import (
    store_memory,
    search_memories,
    recall_for_run,
    link_runs,
    stats as memory_stats,
)
from ai_factory.memory.memory_summarizer import summarize_run
from typing import Optional, List, Dict
from fastapi.responses import JSONResponse, PlainTextResponse
from datetime import datetime, timezone
import os, json, csv
from sqlalchemy import select, func

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
def search_memory(q: str = Query(..., min_length=1), n: Optional[int] = Query(None, ge=1, le=50), limit: Optional[int] = Query(None, ge=1, le=100)):
    # Backward-compatible: if n is provided, perform semantic search; else, text search over entries
    if n is not None and (limit is None):
        results = semantic_search(q, n_results=n)
        hits = []
        ids = results.get("ids", [[]])[0] if results else []
        docs = results.get("documents", [[]])[0] if results else []
        dists = results.get("distances", [[]])[0] if results else []
        for i, doc_id in enumerate(ids):
            hits.append({"id": doc_id, "text": docs[i] if i < len(docs) else None, "distance": dists[i] if i < len(dists) else None})
        return {"query": q, "results": hits}
    # Text search in memory_entries
    lim = limit or 20
    rows = search_memories(q, limit=lim)
    return {"query": q, "results": rows}


@router.get("/snapshot")
def snapshot(limit: int = Query(100, ge=1, le=2000)):
    path = create_snapshot(limit=limit)
    return {"status": "ok", "snapshot": path}


@router.post("/store", status_code=201)
def store(payload: Dict[str, object]):
    try:
        run_id = payload.get("run_id")
        goal = str(payload.get("goal") or "").strip()
        summary = str(payload.get("summary") or "").strip()
        tags = payload.get("tags")
        score = payload.get("score")
        if isinstance(tags, str):
            tags_list = [t.strip() for t in tags.split(",") if t.strip()]
        else:
            tags_list = [str(t).strip() for t in (tags or [])]  # type: ignore
        new_id = store_memory(int(run_id) if run_id is not None else None, goal, summary, tags_list, float(score) if score is not None else None)
        return {"id": new_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/recall/{run_id}")
def recall(run_id: int, limit: int = Query(10, ge=1, le=100)):
    try:
        rows = recall_for_run(run_id, limit=limit)
        return rows
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/learn")
def learn(body: Dict[str, object] | None = None):
    body = body or {}
    run_ids = body.get("runs")
    added = 0
    linked = 0
    runs: List[int] = []
    if isinstance(run_ids, list):
        runs = [int(x) for x in run_ids]
    else:
        # fallback: last 10 orchestrator runs by timestamp
        try:
            from ai_factory.orchestrator.orchestrator_store import list_runs
            runs = [r.id for r in list_runs(limit=10, sort="desc")]
        except Exception:
            runs = []
    # Summarize and store
    stored: List[Dict[str, object]] = []
    for rid in runs:
        try:
            sm = summarize_run(rid)
            try:
                from ai_factory.orchestrator.orchestrator_store import get_run
                rr = get_run(rid)
                goal_text = rr.goal if rr else f"Run {rid}"
            except Exception:
                goal_text = f"Run {rid}"
            mid = store_memory(rid, goal=goal_text, summary=str(sm.get("summary", "")), tags=list(sm.get("tags", [])), score=sm.get("score"))
            stored.append({"run_id": rid, "id": mid, "tags": sm.get("tags", [])})
            added += 1
        except Exception:
            continue
    # Auto-link by tag overlap
    for i in range(len(stored)):
        for j in range(i + 1, len(stored)):
            ti = set([str(t).lower() for t in (stored[i]["tags"] or [])])
            tj = set([str(t).lower() for t in (stored[j]["tags"] or [])])
            ov = ti & tj
            if ov:
                try:
                    link_runs(int(stored[i]["run_id"]), int(stored[j]["run_id"]), reason=f"tag-overlap:{','.join(sorted(ov))}")
                    linked += 1
                except Exception:
                    pass
    return {"added": added, "linked": linked}


@router.get("/stats")
def stats_endpoint():
    return memory_stats()


@router.delete("/{id}")
def delete_memory(id: int):
    from ai_factory.memory.memory_db import SessionLocal, MemoryEntry
    try:
        with SessionLocal() as session:
            row = session.get(MemoryEntry, id)
            if not row:
                raise HTTPException(status_code=404, detail="not found")
            row.deleted = 1
            session.add(row)
            session.commit()
        return {"status": "deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export")
def export_memory(fmt: str = Query("json", pattern="^(json|csv)$")):
    from ai_factory.memory.memory_db import SessionLocal, MemoryEntry
    os.makedirs("ai_factory/data/exports", exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join("ai_factory/data/exports", f"memory_{ts}.{fmt}")
    with SessionLocal() as session:
        rows = list(session.scalars(select(MemoryEntry).where(MemoryEntry.deleted == 0)))
        data = [
            {
                "id": r.id,
                "run_id": r.run_id,
                "goal": r.goal,
                "summary": r.summary,
                "tags": r.tags,
                "score": r.score,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    if fmt == "json":
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    else:
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["id","run_id","goal","summary","tags","score","created_at"]) 
            writer.writeheader()
            for d in data:
                writer.writerow(d)
    return {"status": "ok", "path": path, "count": len(data)}


@router.post("/import")
def import_memory(body: Dict[str, object]):
    items = body.get("items") if isinstance(body, dict) else None
    if not isinstance(items, list):
        raise HTTPException(status_code=400, detail="items must be a list")
    added = 0
    from ai_factory.memory.memory_db import SessionLocal, MemoryEntry
    with SessionLocal() as session:
        for it in items:
            try:
                goal = str(it.get("goal") or "")
                tags = str(it.get("tags") or "")
                # dedupe by goal+tags
                existing = session.scalars(select(MemoryEntry).where(MemoryEntry.goal == goal, MemoryEntry.tags == tags, MemoryEntry.deleted == 0)).first()
                if existing:
                    continue
                row = MemoryEntry(
                    run_id=it.get("run_id"),
                    goal=goal,
                    summary=str(it.get("summary") or ""),
                    tags=tags,
                    score=float(it.get("score")) if it.get("score") is not None else None,
                )
                session.add(row)
                session.commit()
                added += 1
            except Exception:
                continue
    return {"added": added}


@router.get("/diagnostics")
def diagnostics(q: str = Query("")):
    rows = search_memories(q, limit=5) if q else []
    from ai_factory.memory.memory_agent import rank_memories
    ranked = rank_memories(q, rows)
    def score_parts(entry):
        from ai_factory.memory.memory_agent import _hash_vector, _cosine, _tag_overlap_score
        qv = _hash_vector(q)
        ev = _hash_vector((entry.get("summary") or entry.get("goal") or ""))
        sem = _cosine(qv, ev)
        tag = _tag_overlap_score(q, str(entry.get("tags") or ""))
        # recency approx: newer gets higher
        rec = 0.0
        try:
            from datetime import datetime as _dt
            dt = _dt.fromisoformat((entry.get("created_at") or "").replace("Z","+00:00"))
            rec = 1.0 / (1.0 + max(0, (_dt.now() - dt).days))
        except Exception:
            pass
        total = 0.6*sem + 0.25*tag + 0.15*rec
        return {"semantic_score": sem, "tag_score": tag, "recency_score": rec, "total": total}
    matched = [{"id": e.get("id"), **score_parts(e)} for e in ranked]
    agg = matched[0] if matched else {"semantic_score": 0.0, "tag_score": 0.0, "recency_score": 0.0, "total": 0.0}
    return {**agg, "matched": matched}


@router.get("/insights")
def insights():
    s = memory_stats()
    return {"status": "ok", "stats": s}


@router.get("/embeddings/stats")
def embeddings_stats():
    from ai_factory.memory.memory_db import SessionLocal, MemoryEmbedding, MemoryEntry
    with SessionLocal() as session:
        total = session.scalar(select(func.count()).select_from(MemoryEntry).where(MemoryEntry.deleted == 0)) or 0
        emb = session.scalar(select(func.count()).select_from(MemoryEmbedding)) or 0
    return {"total_entries": int(total), "with_embeddings": int(emb)}


@router.get("/links")
def links():
    from ai_factory.memory.memory_db import SessionLocal, MemoryLink
    with SessionLocal() as session:
        rows = list(session.scalars(select(MemoryLink)))
        return [
            {"id": r.id, "source_run": r.source_run, "target_run": r.target_run, "reason": r.reason, "created_at": r.created_at.isoformat() if r.created_at else None}
            for r in rows
        ]


@router.get("/backup")
def backup():
    import os
    if os.getenv("ADMIN_MODE", "false").lower() != "true":
        raise HTTPException(status_code=403, detail="admin only")
    from ai_factory.memory.memory_agent import backup_memory_db
    path = backup_memory_db()
    return {"status": "ok", "path": path}


@router.post("/restore")
def restore():
    import os
    if os.getenv("ADMIN_MODE", "false").lower() != "true":
        raise HTTPException(status_code=403, detail="admin only")
    from ai_factory.memory.memory_agent import restore_latest_backup
    p = restore_latest_backup()
    if not p:
        raise HTTPException(status_code=404, detail="no backup found")
    return {"status": "ok", "path": p}
