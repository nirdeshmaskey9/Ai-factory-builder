from __future__ import annotations

from typing import List

from sqlalchemy import select, desc

from ai_factory.memory.memory_db import SessionLocal, DebuggerRun, init_db


def log_run(request_id: str, language: str, code: str, stdout: str, stderr: str, status: str) -> None:
    """Persist a debugger run result into SQLite."""
    init_db()
    with SessionLocal() as session:
        row = DebuggerRun(
            request_id=request_id,
            language=language,
            code=code,
            stdout=stdout,
            stderr=stderr,
            status=status,
        )
        session.add(row)
        session.commit()


def get_recent(limit: int = 10) -> List[DebuggerRun]:
    with SessionLocal() as session:
        stmt = select(DebuggerRun).order_by(desc(DebuggerRun.timestamp)).limit(limit)
        return list(session.scalars(stmt))


def find_by_request_id(request_id: str) -> List[DebuggerRun]:
    with SessionLocal() as session:
        stmt = select(DebuggerRun).where(DebuggerRun.request_id == request_id).order_by(desc(DebuggerRun.timestamp))
        return list(session.scalars(stmt))


def search_runs(query: str, limit: int = 5) -> List[DebuggerRun]:
    """Very simple LIKE-based search over code/stdout/stderr."""
    like = f"%{query}%"
    with SessionLocal() as session:
        stmt = (
            select(DebuggerRun)
            .where(
                (DebuggerRun.code.like(like))
                | (DebuggerRun.stdout.like(like))
                | (DebuggerRun.stderr.like(like))
            )
            .order_by(desc(DebuggerRun.timestamp))
            .limit(limit)
        )
        return list(session.scalars(stmt))

