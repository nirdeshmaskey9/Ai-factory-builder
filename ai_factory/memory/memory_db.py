from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, select, Float
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.exc import OperationalError
import json
import time

# Data paths (under ai_factory/data/)
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DB_PATH = os.path.join(DATA_DIR, "memory.db")

Base = declarative_base()
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)


class MemoryEvent(Base):
    __tablename__ = "memory_events"
    id = Column(Integer, primary_key=True)
    request_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    task_type = Column(String, nullable=False)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)


class DebuggerRun(Base):
    __tablename__ = "debugger_runs"
    id = Column(Integer, primary_key=True)
    request_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    language = Column(String, nullable=False)
    code = Column(Text, nullable=False)
    stdout = Column(Text, nullable=False)
    stderr = Column(Text, nullable=False)
    status = Column(String, nullable=False)


class SupervisorSession(Base):
    __tablename__ = "supervisor_sessions"
    id = Column(Integer, primary_key=True)
    request_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    goal = Column(Text, nullable=False)
    plan = Column(Text, nullable=False)
    context = Column(Text, nullable=False)
    result = Column(Text, nullable=False)
    status = Column(String, nullable=False)


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"
    id = Column(Integer, primary_key=True)
    build_id = Column(String, index=True, nullable=False)
    domain = Column(String, nullable=False)
    passed = Column(String, nullable=False)  # store as 'true'/'false'
    summary = Column(Text, nullable=False)
    artifacts = Column(Text, nullable=False)  # JSON
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


# Phase 3.0 – Cognitive Memory MCP tables (additive)
class MemoryEntry(Base):
    __tablename__ = "memory_entries"
    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, nullable=True)
    goal = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    tags = Column(Text, nullable=False)  # comma-separated, lowercase
    score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    deleted = Column(Integer, nullable=False, default=0)  # soft delete flag


class MemoryLink(Base):
    __tablename__ = "memory_links"
    id = Column(Integer, primary_key=True)
    source_run = Column(Integer, nullable=False)
    target_run = Column(Integer, nullable=False)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


class MemoryFeedback(Base):
    __tablename__ = "memory_feedback"
    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, nullable=False)
    rating = Column(Integer, nullable=False)  # +1 / -1
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


def init_db() -> None:
    """
    Ensure data directory and SQLite schema are created.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    Base.metadata.create_all(engine)


def get_session() -> Session:
    return SessionLocal()


def _retry_commit(sess: Session, attempts: int = 3) -> None:
    delay = 0.05
    for i in range(attempts):
        try:
            sess.commit()
            return
        except OperationalError:
            time.sleep(delay)
            delay *= 2
    sess.commit()


def store_evaluation(build_id: str, domain: str, passed: bool, summary: str, artifacts: dict) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    Base.metadata.create_all(engine)
    sess = get_session()
    try:
        row = EvaluationResult(
            build_id=build_id,
            domain=domain,
            passed=str(bool(passed)).lower(),
            summary=summary or "Evaluation completed successfully.",
            artifacts=json.dumps(artifacts or {}),
        )
        sess.add(row)
        _retry_commit(sess)
        # Diagnostics log
        try:
            with open(os.path.join(DATA_DIR, "logs", "memory_diagnostics.log"), "a", encoding="utf-8") as f:
                f.write(f"stored evaluation: {build_id}:{domain}\n")
        except Exception:
            pass
    finally:
        sess.close()
