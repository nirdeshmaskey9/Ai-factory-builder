from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select, desc

from ai_factory.memory.memory_db import SessionLocal, Base, init_db
from sqlalchemy import Column, Integer, Text, DateTime, Float, ForeignKey
from datetime import datetime, timezone


class OrchestratorRun(Base):
    __tablename__ = "orchestrator_runs"
    id = Column(Integer, primary_key=True)
    request_id = Column(Text, index=True, nullable=False)
    goal = Column(Text, nullable=False)
    attempt = Column(Integer, nullable=False)
    status = Column(Text, nullable=False)
    plan_json = Column(Text, nullable=False)
    chosen_model = Column(Text, nullable=False)
    context_snippet = Column(Text, nullable=False)
    debugger_stdout = Column(Text, nullable=False)
    debugger_stderr = Column(Text, nullable=False)
    evaluation_score = Column(Float, nullable=False)
    builder_revision_id = Column(Integer, nullable=True)
    deployment_id = Column(Integer, nullable=True)
    notes = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


class OrchestratorRunStep(Base):
    __tablename__ = "orchestrator_run_steps"
    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("orchestrator_runs.id"), index=True, nullable=False)
    step_name = Column(Text, nullable=False)
    step_status = Column(Text, nullable=False)
    log_path = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


def create_run(**fields) -> int:
    init_db()
    with SessionLocal() as session:
        row = OrchestratorRun(**fields)
        session.add(row)
        session.commit()
        return row.id


def update_run(run_id: int, **fields) -> None:
    with SessionLocal() as session:
        row = session.scalars(select(OrchestratorRun).where(OrchestratorRun.id == run_id)).first()
        if not row:
            return
        for k, v in fields.items():
            setattr(row, k, v)
        session.add(row)
        session.commit()


def log_step(run_id: int, step_name: str, step_status: str, log_path: Optional[str] = None) -> int:
    """Record a step for an orchestrator run. Safe to call even if DB not yet initialized."""
    init_db()
    with SessionLocal() as session:
        row = OrchestratorRunStep(
            run_id=run_id,
            step_name=step_name,
            step_status=step_status,
            log_path=log_path or "",
        )
        session.add(row)
        session.commit()
        return row.id


def get_run(run_id: int) -> Optional[OrchestratorRun]:
    with SessionLocal() as session:
        return session.scalars(select(OrchestratorRun).where(OrchestratorRun.id == run_id)).first()


def get_recent(limit: int = 10) -> List[OrchestratorRun]:
    with SessionLocal() as session:
        stmt = select(OrchestratorRun).order_by(desc(OrchestratorRun.timestamp)).limit(limit)
        return list(session.scalars(stmt))
