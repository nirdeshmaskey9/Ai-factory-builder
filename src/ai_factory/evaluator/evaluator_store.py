from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select, desc

from ai_factory.memory.memory_db import SessionLocal, SupervisorSession, Base, init_db
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, Float, Text, DateTime
from datetime import datetime, timezone


class SupervisorEvaluation(Base):
    __tablename__ = "supervisor_evaluations"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, index=True, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    goal = Column(Text, nullable=False)
    score = Column(Float, nullable=False)
    feedback = Column(Text, nullable=False)
    recommendations = Column(Text, nullable=False)
    status = Column(Text, nullable=False)


def save_evaluation(session_id: int, goal: str, score: float, feedback: str, recommendations: str, status: str) -> int:
    init_db()
    with SessionLocal() as session:
        row = SupervisorEvaluation(
            session_id=session_id,
            goal=goal,
            score=score,
            feedback=feedback,
            recommendations=recommendations,
            status=status,
        )
        session.add(row)
        session.commit()
        return row.id


def get_recent(limit: int = 10) -> List[SupervisorEvaluation]:
    with SessionLocal() as session:
        stmt = select(SupervisorEvaluation).order_by(desc(SupervisorEvaluation.timestamp)).limit(limit)
        return list(session.scalars(stmt))


def find_by_session(session_id: int) -> List[SupervisorEvaluation]:
    with SessionLocal() as session:
        stmt = select(SupervisorEvaluation).where(SupervisorEvaluation.session_id == session_id).order_by(
            desc(SupervisorEvaluation.timestamp)
        )
        return list(session.scalars(stmt))


def resolve_session(session_id: Optional[int], goal: Optional[str]) -> Optional[SupervisorSession]:
    with SessionLocal() as session:
        if session_id is not None:
            stmt = select(SupervisorSession).where(SupervisorSession.id == session_id)
            return session.scalars(stmt).first()
        if goal:
            like = f"%{goal}%"
            stmt = select(SupervisorSession).where(SupervisorSession.goal.like(like)).order_by(
                desc(SupervisorSession.timestamp)
            ).limit(1)
            return session.scalars(stmt).first()
        return None

