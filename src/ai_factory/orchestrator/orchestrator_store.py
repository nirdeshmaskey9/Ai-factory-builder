from __future__ import annotations

from typing import List, Optional, Dict, Any

from sqlalchemy import select, desc, asc

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


def list_runs(limit: int = 50, status: Optional[str] = None, sort: str = "desc") -> List[OrchestratorRun]:
    """List recent orchestrator runs with optional status filter and sort order."""
    with SessionLocal() as session:
        stmt = select(OrchestratorRun)
        if status:
            stmt = stmt.where(OrchestratorRun.status == status)
        order = desc if sort.lower() != "asc" else asc
        stmt = stmt.order_by(order(OrchestratorRun.timestamp)).limit(limit)
        return list(session.scalars(stmt))


def get_run_steps(run_id: int) -> List[OrchestratorRunStep]:
    with SessionLocal() as session:
        stmt = select(OrchestratorRunStep).where(OrchestratorRunStep.run_id == run_id).order_by(asc(OrchestratorRunStep.timestamp))
        return list(session.scalars(stmt))


def _read_json(path: str) -> Optional[Dict[str, Any]]:
    try:
        import json, os
        if not path or not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def get_run_summary(run_id: int) -> Dict[str, Any]:
    """Merge run info, steps, and supervisor report JSON. Handles missing artifacts gracefully."""
    r = get_run(run_id)
    if not r:
        return {"not_found": True}

    # Assemble basic run info
    base: Dict[str, Any] = {
        "run": {
            "run_id": r.id,
            "request_id": r.request_id,
            "goal": r.goal,
            "attempt": r.attempt,
            "status": r.status,
            "score": r.evaluation_score,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
        }
    }

    # Paths
    import os
    run_report_path = os.path.join("logs", "orchestrator", f"run_{r.id}.json")
    supervisor_report_path = os.path.join("logs", "supervisor", f"report_{r.id}.json")

    # Read report JSON for duration
    run_report = _read_json(run_report_path) or {}
    base["run"]["duration_sec"] = run_report.get("duration_sec")
    if "advisor_decision" in run_report:
        base["run"]["advisor_decision"] = run_report.get("advisor_decision")
    base["run"]["report_path"] = run_report_path if os.path.exists(run_report_path) else None

    # Steps
    steps = get_run_steps(run_id)
    base["steps"] = [
        {
            "id": s.id,
            "step_name": s.step_name,
            "step_status": s.step_status,
            "log_path": s.log_path or None,
            "timestamp": s.timestamp.isoformat() if s.timestamp else None,
        }
        for s in steps
    ]

    # Supervisor report
    sup = _read_json(supervisor_report_path)
    base["supervisor"] = sup if sup is not None else {"not_found": True}
    if sup is not None:
        base["supervisor"]["report_path"] = supervisor_report_path

    return base
