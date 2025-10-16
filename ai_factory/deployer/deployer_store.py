from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select, desc

from ai_factory.memory.memory_db import SessionLocal, Base, init_db
from sqlalchemy import Column, Integer, Text, DateTime
from datetime import datetime, timezone


class Deployment(Base):
    __tablename__ = "deployments"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, index=True, nullable=True)
    goal = Column(Text, nullable=False)
    port = Column(Integer, nullable=False)
    endpoint = Column(Text, nullable=False)
    version = Column(Text, nullable=False)
    status = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    notes = Column(Text, nullable=False)


def save_deployment(session_id: int | None, goal: str, port: int, endpoint: str, version: str, status: str, notes: str = "") -> int:
    init_db()
    with SessionLocal() as session:
        row = Deployment(
            session_id=session_id,
            goal=goal,
            port=port,
            endpoint=endpoint,
            version=version,
            status=status,
            notes=notes or "",
        )
        session.add(row)
        session.commit()
        return row.id


def update_status(deployment_id: int, status: str, notes: str = "") -> None:
    with SessionLocal() as session:
        stmt = select(Deployment).where(Deployment.id == deployment_id)
        row = session.scalars(stmt).first()
        if row:
            row.status = status
            if notes:
                row.notes = notes
            session.add(row)
            session.commit()


def get_deployment(deployment_id: int) -> Optional[Deployment]:
    with SessionLocal() as session:
        stmt = select(Deployment).where(Deployment.id == deployment_id)
        return session.scalars(stmt).first()


def get_recent(limit: int = 10) -> List[Deployment]:
    with SessionLocal() as session:
        stmt = select(Deployment).order_by(desc(Deployment.timestamp)).limit(limit)
        return list(session.scalars(stmt))

