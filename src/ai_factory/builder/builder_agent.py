from __future__ import annotations

from typing import Any, Dict

from sqlalchemy import select

from ai_factory.evaluator.evaluator_store import SupervisorEvaluation
from ai_factory.memory.memory_db import SessionLocal, SupervisorSession
from ai_factory.services import builder_service as svc
from ai_factory.builder.builder_store import save_revision
from ai_factory.memory.memory_embeddings import add_to_memory


def _get_evaluation(evaluation_id: int) -> SupervisorEvaluation | None:
    with SessionLocal() as session:
        stmt = select(SupervisorEvaluation).where(SupervisorEvaluation.id == evaluation_id)
        return session.scalars(stmt).first()


def _get_session(session_id: int) -> SupervisorSession | None:
    with SessionLocal() as session:
        stmt = select(SupervisorSession).where(SupervisorSession.id == session_id)
        return session.scalars(stmt).first()


def rebuild(evaluation_id: int) -> Dict[str, Any]:
    ev = _get_evaluation(evaluation_id)
    if not ev:
        raise ValueError("evaluation not found")

    sess = _get_session(ev.session_id)
    if not sess:
        raise ValueError("referenced supervisor session not found")

    old_score = float(ev.score)
    goal = sess.goal
    patch = svc.make_patch(goal, sess.plan, sess.context, sess.result, ev.feedback)

    applied = svc.apply_and_rerun(goal, patch)
    new_eval = svc.evaluate_session(applied["session_id"]) if applied.get("session_id", -1) != -1 else {"score": old_score}
    new_score = float(new_eval.get("score", old_score))

    status = svc.status_from_delta(old_score, new_score)
    rev_id = save_revision(
        evaluation_id=evaluation_id,
        old_score=old_score,
        new_score=new_score,
        diff_summary=patch["diff_summary"],
        status=status,
        notes=patch.get("notes", ""),
    )

    # Memory snippet
    snippet = svc.memory_snippet(rev_id, evaluation_id, old_score, new_score, patch["diff_summary"])
    add_to_memory(f"rebuild:{rev_id}", snippet)

    return {
        "revision_id": rev_id,
        "evaluation_id": evaluation_id,
        "old_score": old_score,
        "new_score": new_score,
        "diff_summary": patch["diff_summary"],
        "status": status,
        "notes": patch.get("notes", ""),
    }

