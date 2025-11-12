from __future__ import annotations

from typing import List, Dict, Any, Optional
import json

from sqlalchemy import text

from ai_factory.memory.memory_db import SessionLocal, DialogueTurn, DialogueSummary, init_db


def _ensure_db():
    try:
        init_db()
    except Exception:
        pass


def save_turn(session_id: str, role: str, content: str, meta: Optional[Dict[str, Any]] = None) -> int:
    """
    Append a turn to dialogue_turns.
    Returns inserted id.
    """
    _ensure_db()
    with SessionLocal() as sess:
        try:
            # Guard query using sqlalchemy.text to avoid warnings
            sess.execute(text("SELECT 1"))
        except Exception:
            pass
        row = DialogueTurn(
            session_id=str(session_id or "default"),
            role=str(role or "user"),
            content=str(content or ""),
            meta=json.dumps(meta or {}),
        )
        sess.add(row)
        sess.commit()
        return int(row.id)


def load_recent(session_id: str, n: int = 40) -> List[Dict[str, Any]]:
    _ensure_db()
    n = int(n or 40)
    sid = str(session_id or "default")
    # Map 'current' to default UI session alias
    if sid.lower() == "current":
        sid = "ui-session"
    with SessionLocal() as sess:
        try:
            sess.execute(text("SELECT 1"))
        except Exception:
            pass
        q = (
            sess.query(DialogueTurn)
            .filter(DialogueTurn.session_id == sid)
            .order_by(DialogueTurn.id.desc())
            .limit(n)
        )
        rows = list(q)
        out: List[Dict[str, Any]] = []
        for r in reversed(rows):
            try:
                meta = json.loads(r.meta or "{}")
            except Exception:
                meta = {}
            out.append(
                {
                    "id": int(r.id),
                    "session_id": r.session_id,
                    "role": r.role,
                    "content": r.content,
                    "meta": meta,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                }
            )
        return out


def save_session_summary(session_id: str, summary_json: Dict[str, Any]) -> int:
    _ensure_db()
    with SessionLocal() as sess:
        try:
            sess.execute(text("SELECT 1"))
        except Exception:
            pass
        row = DialogueSummary(
            session_id=str(session_id or "default"),
            summary=json.dumps(summary_json or {}),
        )
        sess.add(row)
        sess.commit()
        return int(row.id)


def list_summaries(limit_newest: int = 3, limit_oldest: int = 3) -> List[Dict[str, Any]]:
    """
    Return up to 6 summaries: newest N and oldest N.
    """
    _ensure_db()
    with SessionLocal() as sess:
        newest = (
            sess.query(DialogueSummary)
            .order_by(DialogueSummary.id.desc())
            .limit(int(limit_newest or 3))
            .all()
        )
        oldest = (
            sess.query(DialogueSummary)
            .order_by(DialogueSummary.id.asc())
            .limit(int(limit_oldest or 3))
            .all()
        )
        rows = oldest + list(reversed(newest))
        out: List[Dict[str, Any]] = []
        for r in rows:
            try:
                s = json.loads(r.summary or "{}")
            except Exception:
                s = {}
            out.append(
                {
                    "id": int(r.id),
                    "session_id": r.session_id,
                    "summary": s,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
            )
        return out
