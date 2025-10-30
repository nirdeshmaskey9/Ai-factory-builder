from __future__ import annotations

from sqlalchemy.exc import OperationalError
from sqlalchemy import text
from pathlib import Path
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone

from sqlalchemy import select, func, and_, or_, desc

from ai_factory.memory.memory_db import (
    engine,
    init_db,
    SessionLocal,
    MemoryEntry,
    MemoryLink,
    MemoryEmbedding,
)
from shutil import copy2
import os


def startup_probe() -> None:
    """Attempt a trivial insert/select/delete cycle to validate DB connectivity.

    Writes diagnostics to ./logs/memory.log. Retries on lock.
    """
    init_db()
    Path("logs").mkdir(exist_ok=True)
    log = Path("logs/memory.log")
    attempts = 0
    while attempts < 3:
        attempts += 1
        try:
            with engine.begin() as conn:
                conn.execute(text("CREATE TABLE IF NOT EXISTS _probe (id INTEGER PRIMARY KEY, v TEXT)"))
                conn.execute(text("INSERT INTO _probe(v) VALUES ('ok')"))
                rows = list(conn.execute(text("SELECT count(*) FROM _probe")))
                conn.execute(text("DELETE FROM _probe"))
            log.write_text((log.read_text(encoding="utf-8") if log.exists() else "") + f"probe ok rows={rows[0][0]}\n", encoding="utf-8")
            return
        except OperationalError:
            time.sleep(0.05 * attempts)
        except Exception as e:
            # Log and exit silently
            log.write_text((log.read_text(encoding="utf-8") if log.exists() else "") + f"probe error: {e}\n", encoding="utf-8")
            return



# ---- Phase 3.0 – Cognitive Memory MCP helpers ----

def _norm_tags(tags: List[str]) -> str:
    seen = []
    for t in tags:
        tt = str(t).strip().lower()
        if tt and tt not in seen:
            seen.append(tt)
    return ",".join(seen)


def store_memory(run_id: Optional[int], goal: str, summary: str, tags: List[str], score: Optional[float]) -> int:
    init_db()
    with SessionLocal() as session:
        row = MemoryEntry(
            run_id=run_id,
            goal=str(goal or "").strip(),
            summary=str(summary or "").strip(),
            tags=_norm_tags(tags or []),
            score=score if score is not None else None,
        )
        session.add(row)
        session.commit()
        return row.id


def search_memories(q: str, limit: int = 20) -> List[Dict]:
    q = (q or "").strip()
    init_db()
    with SessionLocal() as session:
        tokens = [t for t in q.lower().split() if t]
        conditions = []
        if tokens:
            for tok in tokens:
                like = f"%{tok}%"
                conditions.append(
                    or_(
                        func.lower(MemoryEntry.goal).like(like),
                        func.lower(MemoryEntry.summary).like(like),
                        func.lower(MemoryEntry.tags).like(like),
                    )
                )
        else:
            like = f"%{q.lower()}%"
            conditions.append(
                or_(
                    func.lower(MemoryEntry.goal).like(like),
                    func.lower(MemoryEntry.summary).like(like),
                    func.lower(MemoryEntry.tags).like(like),
                )
            )
        stmt = select(MemoryEntry).where(and_(MemoryEntry.deleted == 0, or_(*conditions))).order_by(desc(MemoryEntry.created_at)).limit(int(limit or 20))
        rows = list(session.scalars(stmt))
        out: List[Dict] = []
        for r in rows:
            out.append(
                {
                    "id": r.id,
                    "run_id": r.run_id,
                    "goal": r.goal,
                    "summary": r.summary,
                    "tags": r.tags,
                    "score": r.score,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
            )
        ranked = rank_memories(q, out)
        return ranked[: int(limit or 20)]


def _split_tags(s: str) -> List[str]:
    return [t for t in (s or "").split(",") if t]


def recall_for_run(run_id: int, limit: int = 10) -> List[Dict]:
    # derive keywords from goal of the given run if present in entries
    init_db()
    with SessionLocal() as session:
        me = session.scalars(
            select(MemoryEntry).where(MemoryEntry.run_id == run_id, MemoryEntry.deleted == 0).limit(1)
        ).first()
        keytags = set(_split_tags(me.tags) if me else [])

        stmt = select(MemoryEntry).where(MemoryEntry.deleted == 0)
        rows = [r for r in session.scalars(stmt) if (r.run_id or -1) != run_id]
        # Rank by tag overlap + score; fallback to recency
        def rank(r: MemoryEntry) -> float:
            tags = set(_split_tags(r.tags))
            overlap = len(tags & keytags)
            sc = float(r.score) if r.score is not None else 0.0
            rec = r.created_at.timestamp() if getattr(r, "created_at", None) else 0.0
            return overlap * 10.0 + sc + rec * 1e-9

        # Prefer candidates that share at least one tag; if none, fall back to all
        with_overlap = [r for r in rows if len(set(_split_tags(r.tags)) & keytags) > 0]
        cand = with_overlap if with_overlap else rows
        cand.sort(key=rank, reverse=True)
        # Ensure newest overlaps are represented first
        try:
            recent = sorted(with_overlap, key=lambda r: (r.created_at or 0), reverse=True)
        except Exception:
            recent = with_overlap
        ordered: list[MemoryEntry] = []
        for r in recent[:3]:
            if r not in ordered:
                ordered.append(r)
        for r in cand:
            if len(ordered) >= int(limit or 10):
                break
            if r not in ordered:
                ordered.append(r)
        rows = ordered[: int(limit or 10)]
        out = [
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
        # Further rank via semantic + tag + recency based on goal text
        return rank_memories(me.goal if me else "", out)[: int(limit or 10)]


def link_runs(source_run: int, target_run: int, reason: str) -> int:
    init_db()
    with SessionLocal() as session:
        row = MemoryLink(source_run=source_run, target_run=target_run, reason=str(reason or "").strip())
        session.add(row)
        session.commit()
        return row.id


def stats() -> Dict[str, object]:
    init_db()
    with SessionLocal() as session:
        total = session.scalar(select(func.count()).select_from(MemoryEntry).where(MemoryEntry.deleted == 0)) or 0
        # recent 7 days
        # SQLite lacks timezone; compare ISO timestamps via datetime in Python
        rows = list(session.scalars(select(MemoryEntry).where(MemoryEntry.deleted == 0)))
        now = datetime.now(timezone.utc)
        recent = 0
        last_created = None
        scores: List[float] = []
        tag_counts: Dict[str, int] = {}
        for r in rows:
            if r.created_at:
                dt = r.created_at
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                last_created = max(last_created, dt) if last_created else dt
                if (now - dt).days <= 7:
                    recent += 1
            if r.score is not None:
                try:
                    scores.append(float(r.score))
                except Exception:
                    pass
            for t in _split_tags(r.tags):
                tag_counts[t] = tag_counts.get(t, 0) + 1
        avg_score = sum(scores) / len(scores) if scores else None
        tags_list = [{"tag": k, "count": v} for k, v in sorted(tag_counts.items(), key=lambda x: (-x[1], x[0]))]
        return {
            "total": int(total),
            "recent_7d": int(recent),
            "avg_score": avg_score,
            "tags": tags_list[:20],
            "last_created_at": last_created.isoformat() if last_created else None,
        }


# UI/Backend safety helper for tag handling
def safe_tags(entry: Dict[str, object]):
    tags = entry.get("tags") if isinstance(entry, dict) else None
    if not tags:
        return []
    if isinstance(tags, list):
        return [str(t).strip() for t in tags if str(t).strip()]
    return [t.strip() for t in str(tags).split(',') if t.strip()]


def auto_learn_from_run(run_id: Optional[int], goal: Optional[str], summary: Optional[str], tags: Optional[List[str]] = None) -> int:
    """Summarize and store/update memory for a run. Upsert by run_id.
    Returns memory entry id.
    """
    init_db()
    goal_text = (goal or "").strip()
    summ_text = (summary or "").strip()
    # Derive tags: from provided or from goal keywords
    tlist = [str(t).strip().lower() for t in (tags or []) if str(t).strip()] if tags else []
    for w in (goal_text.split()[:5] if goal_text else []):
        lw = w.strip().lower()
        if lw and lw not in tlist:
            tlist.append(lw)
    with SessionLocal() as session:
        existing = None
        if run_id is not None:
            existing = session.scalars(select(MemoryEntry).where(MemoryEntry.run_id == run_id, MemoryEntry.deleted == 0)).first()
        if existing:
            existing.goal = existing.goal or goal_text
            if summ_text:
                existing.summary = summ_text
            if tlist:
                existing.tags = _norm_tags(_split_tags(existing.tags) + tlist)
            session.add(existing)
            session.commit()
            return existing.id
        else:
            row = MemoryEntry(run_id=run_id, goal=goal_text or (f"Run {run_id}" if run_id is not None else ""), summary=summ_text or goal_text, tags=_norm_tags(tlist), score=None)
            session.add(row)
            session.commit()
            return row.id


def backup_memory_db() -> str:
    from ai_factory.memory.memory_db import DB_PATH
    ts = datetime.now().strftime("%Y%m%dT%H%M%SZ")
    out_dir = os.path.join("ai_factory", "data", "backups")
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, f"memory_backup_{ts}.db")
    copy2(DB_PATH, dst)
    return dst


def restore_latest_backup() -> Optional[str]:
    out_dir = os.path.join("ai_factory", "data", "backups")
    if not os.path.exists(out_dir):
        return None
    files = sorted([f for f in os.listdir(out_dir) if f.startswith("memory_backup_") and f.endswith(".db")])
    if not files:
        return None
    latest = files[-1]
    from ai_factory.memory.memory_db import DB_PATH
    copy2(os.path.join(out_dir, latest), DB_PATH)
    return os.path.join(out_dir, latest)


# --- Embedding support ---
def _hash_vector(text: str, dim: int = 64) -> List[float]:
    import hashlib
    h = hashlib.sha256((text or "").encode("utf-8")).digest()
    # expand to dim by repeating digest
    by = (h * ((dim + len(h) - 1) // len(h)))[:dim]
    # normalize bytes to 0..1 floats
    vec = [b / 255.0 for b in by]
    return vec


def _cosine(a: List[float], b: List[float]) -> float:
    import math
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def ensure_embedding(entry: MemoryEntry) -> List[float]:
    init_db()
    with SessionLocal() as session:
        existing = session.scalars(select(MemoryEmbedding).where(MemoryEmbedding.entry_id == entry.id)).first()
        if existing:
            try:
                data = existing.vector.decode("utf-8")
                import json
                return json.loads(data)
            except Exception:
                pass
        # Fallback deterministic embedding via hash
        text = f"{entry.goal}\n{entry.summary}\n{entry.tags}"
        vec = _hash_vector(text)
        import json
        payload = json.dumps(vec).encode("utf-8")
        row = existing or MemoryEmbedding(entry_id=entry.id, vector=payload)
        row.vector = payload
        row.updated_at = datetime.now()  # naive ok for SQLite
        session.add(row)
        session.commit()
        return vec


def _tag_overlap_score(query: str, tags_csv: str) -> float:
    q_tokens = [w.strip().lower() for w in query.split() if w.strip()]
    tags = [t.strip().lower() for t in (tags_csv or "").split(",") if t.strip()]
    if not q_tokens or not tags:
        return 0.0
    inter = len(set(q_tokens) & set(tags))
    return inter / max(1, len(set(tags)))


def rank_memories(query: str, rows: List[Dict]) -> List[Dict]:
    import os
    def _w(name: str, default: float) -> float:
        try:
            return float(os.getenv(name, str(default)))
        except Exception:
            return default
    W_SEM = _w('AI_FACTORY_MEMORY_WEIGHT_SEMANTIC', 0.6)
    W_TAG = _w('AI_FACTORY_MEMORY_WEIGHT_TAG', 0.25)
    W_REC = _w('AI_FACTORY_MEMORY_WEIGHT_RECENCY', 0.15)

    qvec = _hash_vector(query or "")
    scored: List[Tuple[float, Dict]] = []
    now = datetime.now(timezone.utc)
    for r in rows:
        # compute
        try:
            created_at = r.get("created_at")
            if isinstance(created_at, str):
                try:
                    dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                except Exception:
                    dt = now
            else:
                dt = now
            # Ensure dt is aware
            if dt.tzinfo is None:
                from datetime import timezone as _tz
                dt = dt.replace(tzinfo=_tz.utc)
            days = max(0.0, (now - dt).days)
            recency = 1.0 / (1.0 + days)
        except Exception:
            recency = 0.0
        tag_score = _tag_overlap_score(query or "", str(r.get("tags") or ""))
        # semantic by ensuring embedding of row if possible
        try:
            with SessionLocal() as session:
                e = session.get(MemoryEntry, int(r.get("id")))
                vec = ensure_embedding(e) if e else _hash_vector((r.get("summary") or r.get("goal") or ""))
        except Exception:
            vec = _hash_vector((r.get("summary") or r.get("goal") or ""))
        sem = _cosine(qvec, vec)
        total = (W_SEM * sem) + (W_TAG * tag_score) + (W_REC * recency)
        scored.append((total, r))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in scored]


def log_model_usage(**kwargs) -> int:
    """Insert a model usage row. kwargs may include: run_id, step, role, backend, model, latency_ms, tokens_in, tokens_out, success.
    Returns inserted id (best-effort).
    """
    init_db()
    from ai_factory.memory.memory_db import SessionLocal, ModelUsage
    with SessionLocal() as session:
        row = ModelUsage(
            run_id=str(kwargs.get("run_id")) if kwargs.get("run_id") is not None else None,
            step=str(kwargs.get("step") or ""),
            role=str(kwargs.get("role") or ""),
            backend=str(kwargs.get("backend") or ""),
            model=str(kwargs.get("model") or ""),
            latency_ms=int(kwargs.get("latency_ms") or 0),
            tokens_in=int(kwargs.get("tokens_in") or 0),
            tokens_out=int(kwargs.get("tokens_out") or 0),
            success=bool(kwargs.get("success")) if kwargs.get("success") is not None else None,
        )
        session.add(row)
        session.commit()
        return row.id


# ---- Bridge helpers (Phase 3.3) ----
def generate_context_summary(conversation_id: str) -> str:
    """Produce a short, lossless summary based on recent related memories.

    We treat conversation_id as a loose key and derive a summary by
    selecting the most relevant memories to that key.
    """
    key = str(conversation_id or "").strip()
    if not key:
        return ""
    related = search_memories(key, limit=5)
    parts = []
    for r in related:
        segment = r.get("summary") or r.get("goal") or ""
        if segment:
            parts.append(str(segment).strip())
    joined = " \n".join(parts)
    # Lightweight semantic compression: truncate gracefully around sentence boundaries
    if len(joined) > 480:
        joined = joined[:480].rsplit(".", 1)[0] + "."
    return joined


def tag_context_relevance(query: str, top_n: int = 10) -> list[dict]:
    """Rank memories by cosine + recency weighting using existing rank_memories."""
    rows = search_memories(query or "", limit=top_n)
    return rows
