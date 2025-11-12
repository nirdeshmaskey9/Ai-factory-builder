from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Iterable, List, Dict, Any

from sqlalchemy import select, desc

from ai_factory.memory.memory_db import SessionLocal, MemoryEvent, init_db, DATA_DIR

# Snapshots directory
SNAPSHOT_DIR = os.path.join(DATA_DIR, "snapshots")


def log_event(request_id: str, task_type: str, prompt: str, response: str) -> None:
    """
    Append a new planner dispatch event (request+response) to SQLite.
    """
    # Ensure DB is initialized (safe to call repeatedly)
    init_db()
    with SessionLocal() as session:
        evt = MemoryEvent(
            request_id=request_id,
            task_type=task_type,
            prompt=prompt,
            response=response,
        )
        session.add(evt)
        session.commit()


def get_recent(limit: int = 10) -> List[MemoryEvent]:
    """
    Return latest events (most recent first).
    """
    with SessionLocal() as session:
        stmt = select(MemoryEvent).order_by(desc(MemoryEvent.timestamp)).limit(limit)
        return list(session.scalars(stmt))


def find_by_request_id(request_id: str) -> List[MemoryEvent]:
    with SessionLocal() as session:
        stmt = select(MemoryEvent).where(MemoryEvent.request_id == request_id).order_by(desc(MemoryEvent.timestamp))
        return list(session.scalars(stmt))


def create_snapshot(limit: int = 100) -> str:
    """
    Write a JSONL snapshot of the most recent events.
    Returns absolute file path to the snapshot.
    """
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    now = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(SNAPSHOT_DIR, f"events_{now}.jsonl")

    records = []
    for e in get_recent(limit=limit):
        records.append({
            "id": e.id,
            "request_id": e.request_id,
            "timestamp": e.timestamp.isoformat(),
            "task_type": e.task_type,
            "prompt": e.prompt,
            "response": e.response,
        })

    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return path
