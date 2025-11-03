from __future__ import annotations

from typing import Literal
from sqlalchemy import text

from ai_factory.memory.memory_db import SessionLocal, MoodLog, init_db


Mood = Literal["upbeat", "neutral", "stressed", "sad", "focused"]


def analyze_mood(user_text: str) -> Mood:
    t = (user_text or "").lower()
    if any(w in t for w in ["stressed", "overwhelmed", "anxious", "panic", "busy"]):
        return "stressed"
    if any(w in t for w in ["sad", "depressed", "down"]):
        return "sad"
    if any(w in t for w in ["focus", "focused", "concentrate", "deadline"]):
        return "focused"
    if any(w in t for w in ["great", "good", "awesome", "happy", "excited"]):
        return "upbeat"
    return "neutral"


def log_mood(session_id: str, mood: Mood) -> int:
    init_db()
    with SessionLocal() as sess:
        try:
            sess.execute(text("SELECT 1"))
        except Exception:
            pass
        row = MoodLog(session_id=str(session_id or "default"), mood=mood)
        sess.add(row)
        sess.commit()
        return int(row.id)

