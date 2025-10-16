from __future__ import annotations

from typing import List, Tuple

from sqlalchemy import select, desc, func

from ai_factory.memory.memory_db import SessionLocal, Base, init_db
from sqlalchemy import Column, Integer, Text, DateTime, Float
from datetime import datetime, timezone


class EvaluationRewardLog(Base):
    __tablename__ = "evaluation_reward_log"
    id = Column(Integer, primary_key=True)
    model_name = Column(Text, nullable=False)
    task_type = Column(Text, nullable=False)
    score_delta = Column(Float, nullable=False)
    reward = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    notes = Column(Text, nullable=False)


def log_reward(model_name: str, task_type: str, score_delta: float, reward: float, notes: str = "") -> int:
    init_db()
    with SessionLocal() as session:
        row = EvaluationRewardLog(
            model_name=model_name,
            task_type=task_type,
            score_delta=float(score_delta),
            reward=float(reward),
            notes=notes or "",
        )
        session.add(row)
        session.commit()
        return row.id


def recent_rewards(limit: int = 10) -> List[EvaluationRewardLog]:
    with SessionLocal() as session:
        stmt = select(EvaluationRewardLog).order_by(desc(EvaluationRewardLog.timestamp)).limit(limit)
        return list(session.scalars(stmt))


def avg_reward_per_model() -> List[Tuple[str, float]]:
    with SessionLocal() as session:
        stmt = (
            select(EvaluationRewardLog.model_name, func.avg(EvaluationRewardLog.reward))
            .group_by(EvaluationRewardLog.model_name)
        )
        return [(m, float(avg)) for m, avg in session.execute(stmt)]

