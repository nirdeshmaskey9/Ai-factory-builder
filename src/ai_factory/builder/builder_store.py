from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select, desc

from ai_factory.memory.memory_db import SessionLocal, Base, init_db
from sqlalchemy import Column, Integer, Float, Text, DateTime
from datetime import datetime, timezone


class BuilderRevision(Base):
    __tablename__ = "builder_revisions"
    id = Column(Integer, primary_key=True)
    evaluation_id = Column(Integer, index=True, nullable=False)
    old_score = Column(Float, nullable=False)
    new_score = Column(Float, nullable=False)
    diff_summary = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    status = Column(Text, nullable=False)
    notes = Column(Text, nullable=False)


def save_revision(evaluation_id: int, old_score: float, new_score: float, diff_summary: str, status: str, notes: str = "") -> int:
    init_db()
    with SessionLocal() as session:
        row = BuilderRevision(
            evaluation_id=evaluation_id,
            old_score=old_score,
            new_score=new_score,
            diff_summary=diff_summary,
            status=status,
            notes=notes or "",
        )
        session.add(row)
        session.commit()
        return row.id


def get_revision(revision_id: int) -> Optional[BuilderRevision]:
    with SessionLocal() as session:
        stmt = select(BuilderRevision).where(BuilderRevision.id == revision_id)
        return session.scalars(stmt).first()


def get_recent(limit: int = 10) -> List[BuilderRevision]:
    with SessionLocal() as session:
        stmt = select(BuilderRevision).order_by(desc(BuilderRevision.timestamp)).limit(limit)
        return list(session.scalars(stmt))

