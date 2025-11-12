from __future__ import annotations

import json
from typing import List

from sqlalchemy import select, desc

from ai_factory.memory.memory_db import SessionLocal, SupervisorSession, init_db


def save_session(request_id: str, goal: str, plan_json: str, context_text: str, result_text: str, status: str) -> int:
    init_db()
    with SessionLocal() as session:
        row = SupervisorSession(
            request_id=request_id,
            goal=goal,
            plan=plan_json,
            context=context_text,
            result=result_text,
            status=status,
        )
        session.add(row)
        session.commit()
        return row.id


def get_recent(limit: int = 10) -> List[SupervisorSession]:
    with SessionLocal() as session:
        stmt = select(SupervisorSession).order_by(desc(SupervisorSession.timestamp)).limit(limit)
        return list(session.scalars(stmt))


def get_latest(limit: int = 10) -> List[SupervisorSession]:
    return get_recent(limit=limit)

