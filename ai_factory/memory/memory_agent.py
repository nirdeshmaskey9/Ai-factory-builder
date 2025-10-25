from __future__ import annotations

from sqlalchemy.exc import OperationalError
from sqlalchemy import text
from pathlib import Path
import time
from typing import List, Dict, Optional
from datetime import datetime

from sqlalchemy import select, func, and_, or_, desc

from ai_factory.memory.memory_db import (
    engine,
    init_db,
    SessionLocal,
    MemoryEntry,
    MemoryLink,
)


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
        like = f"%{q.lower()}%"
        stmt = (
            select(MemoryEntry)
            .where(
                and_(
                    MemoryEntry.deleted == 0,
                    or_(
                        func.lower(MemoryEntry.goal).like(like),
                        func.lower(MemoryEntry.summary).like(like),
                        func.lower(MemoryEntry.tags).like(like),
                    ),
                )
            )
            .order_by(desc(MemoryEntry.created_at))
            .limit(int(limit or 20))
        )
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
        return out


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

        rows.sort(key=rank, reverse=True)
        rows = rows[: int(limit or 10)]
        return [
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
        now = datetime.utcnow()  # type: ignore
        recent = 0
        last_created = None
        scores: List[float] = []
        tag_counts: Dict[str, int] = {}
        for r in rows:
            if r.created_at:
                last_created = max(last_created, r.created_at) if last_created else r.created_at
                if (now - r.created_at).days <= 7:
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
