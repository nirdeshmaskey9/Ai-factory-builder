from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from pathlib import Path
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy import create_engine, Column, Integer, Text, select, desc
from datetime import datetime, timezone


DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
DB_URL = f"sqlite:///{(DATA_DIR / 'feedback.db').as_posix()}"
engine = create_engine(DB_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)
Base = declarative_base()


class FeedbackEntry(Base):
    __tablename__ = "feedback_entries"
    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, nullable=False, index=True)
    rating = Column(Text, nullable=False)  # 'up' | 'down'
    comment = Column(Text, nullable=False)
    ts = Column(Text, default=lambda: datetime.now(timezone.utc).isoformat(), nullable=False)


Base.metadata.create_all(engine)


class FeedbackIn(BaseModel):
    run_id: int
    rating: str
    comment: str | None = ""


router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.post("")
def create_feedback(payload: FeedbackIn) -> Dict[str, Any]:
    rating = (payload.rating or "").strip().lower()
    if rating not in ("up", "down"):
        raise HTTPException(status_code=400, detail="rating must be 'up' or 'down'")
    with SessionLocal() as session:
        row = FeedbackEntry(run_id=int(payload.run_id), rating=rating, comment=(payload.comment or ""))
        session.add(row)
        session.commit()
        return {"status": "ok", "id": row.id}


@router.get("/{run_id}")
def list_for_run(run_id: int) -> List[Dict[str, Any]]:
    with SessionLocal() as session:
        stmt = select(FeedbackEntry).where(FeedbackEntry.run_id == run_id).order_by(desc(FeedbackEntry.ts))
        return [
            {"id": r.id, "run_id": r.run_id, "rating": r.rating, "comment": r.comment, "ts": r.ts}
            for r in session.scalars(stmt)
        ]


@router.get("/all")
def list_all(limit: int = 200) -> List[Dict[str, Any]]:
    with SessionLocal() as session:
        stmt = select(FeedbackEntry).order_by(desc(FeedbackEntry.ts)).limit(limit)
        return [
            {"id": r.id, "run_id": r.run_id, "rating": r.rating, "comment": r.comment, "ts": r.ts}
            for r in session.scalars(stmt)
        ]
