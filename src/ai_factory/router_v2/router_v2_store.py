from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select, desc, update

from ai_factory.memory.memory_db import SessionLocal, Base, init_db
from sqlalchemy import Column, Integer, Text, DateTime, Float
from datetime import datetime, timezone


class ModelRegistry(Base):
    __tablename__ = "model_registry"
    id = Column(Integer, primary_key=True)
    model_name = Column(Text, unique=True, nullable=False)
    capabilities = Column(Text, nullable=False)  # CSV or JSON-ish string
    weight = Column(Float, nullable=False, default=1.0)
    avg_latency_ms = Column(Float, nullable=False, default=400.0)
    avg_cost = Column(Float, nullable=False, default=1.0)
    success_rate = Column(Float, nullable=False, default=0.9)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


class ModelRoutingLog(Base):
    __tablename__ = "model_routing_log"
    id = Column(Integer, primary_key=True)
    task_type = Column(Text, nullable=False)
    model_name = Column(Text, nullable=False)
    duration_ms = Column(Float, nullable=False)
    score = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


def _ensure_seed() -> None:
    init_db()
    with SessionLocal() as session:
        existing = set(r.model_name for r in session.scalars(select(ModelRegistry)))
        seeds = [
            ("gpt4", "planning,logic,general", 1.0, 420.0, 1.2, 0.92),
            ("claude3", "coding,reasoning,general", 1.0, 350.0, 1.0, 0.9),
            ("gemini", "design,ui,vision,general", 1.0, 300.0, 0.9, 0.88),
        ]
        changed = False
        for name, caps, w, lat, cost, sr in seeds:
            if name not in existing:
                session.add(ModelRegistry(model_name=name, capabilities=caps, weight=w, avg_latency_ms=lat, avg_cost=cost, success_rate=sr))
                changed = True
        if changed:
            session.commit()


def list_models() -> List[ModelRegistry]:
    _ensure_seed()
    with SessionLocal() as session:
        return list(session.scalars(select(ModelRegistry).order_by(ModelRegistry.model_name)))


def upsert_model(model_name: str, capabilities: Optional[List[str]] = None, weight: Optional[float] = None) -> None:
    _ensure_seed()
    with SessionLocal() as session:
        row = session.scalars(select(ModelRegistry).where(ModelRegistry.model_name == model_name)).first()
        if row:
            if capabilities is not None:
                row.capabilities = ",".join(capabilities)
            if weight is not None:
                row.weight = float(weight)
            row.updated_at = datetime.now(timezone.utc)
            session.add(row)
            session.commit()
        else:
            caps = ",".join(capabilities or ["general"])
            session.add(ModelRegistry(model_name=model_name, capabilities=caps, weight=float(weight or 1.0)))
            session.commit()


def log_routing(task_type: str, model_name: str, duration_ms: float, score: float) -> int:
    _ensure_seed()
    with SessionLocal() as session:
        row = ModelRoutingLog(task_type=task_type, model_name=model_name, duration_ms=float(duration_ms), score=float(score))
        session.add(row)
        # update rolling averages on registry (very simple EMA)
        reg = session.scalars(select(ModelRegistry).where(ModelRegistry.model_name == model_name)).first()
        if reg:
            alpha = 0.3
            reg.avg_latency_ms = (1 - alpha) * reg.avg_latency_ms + alpha * float(duration_ms)
            # mock success rate drift slightly towards score
            reg.success_rate = (1 - alpha) * reg.success_rate + alpha * float(score)
            reg.updated_at = datetime.now(timezone.utc)
            session.add(reg)
        session.commit()
        return row.id


def recent_logs(limit: int = 10) -> List[ModelRoutingLog]:
    _ensure_seed()
    with SessionLocal() as session:
        return list(session.scalars(select(ModelRoutingLog).order_by(desc(ModelRoutingLog.timestamp)).limit(limit)))

