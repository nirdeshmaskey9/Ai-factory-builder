from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, select
from sqlalchemy.orm import declarative_base, sessionmaker, Session

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
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    task_type = Column(String, nullable=False)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)


class DebuggerRun(Base):
    __tablename__ = "debugger_runs"
    id = Column(Integer, primary_key=True)
    request_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    language = Column(String, nullable=False)
    code = Column(Text, nullable=False)
    stdout = Column(Text, nullable=False)
    stderr = Column(Text, nullable=False)
    status = Column(String, nullable=False)


def init_db() -> None:
    """
    Ensure data directory and SQLite schema are created.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    Base.metadata.create_all(engine)


def get_session() -> Session:
    return SessionLocal()
