from __future__ import annotations

import json
from typing import Any, Dict, Optional

from ai_factory.evaluator.evaluator_store import (
    resolve_session,
    save_evaluation,
)
from ai_factory.services.evaluator_service import (
    compute_score,
    derive_status,
    summarize_feedback,
    make_memory_snippet,
)
from ai_factory.memory.memory_embeddings import add_to_memory


def evaluate(session_id: Optional[int] = None, goal: Optional[str] = None) -> Dict[str, Any]:
    sess = resolve_session(session_id, goal)
    if not sess:
        raise ValueError("No matching supervisor session found")

    plan_json = sess.plan or "{}"
    context_text = sess.context or ""
    result_text = sess.result or ""
    goal_text = sess.goal or (goal or "")

    score = compute_score(goal_text, plan_json, context_text, result_text)
    status = derive_status(score)
    feedback, recs = summarize_feedback(goal_text, plan_json, context_text, result_text, score)

    eval_id = save_evaluation(session_id=sess.id, goal=goal_text, score=score, feedback=feedback, recommendations=recs, status=status)

    # Inject feedback into vector memory for future recall
    snippet = make_memory_snippet(eval_id, sess.id, goal_text, score, feedback, recs)
    add_to_memory(f"eval:{eval_id}", snippet)

    return {
        "evaluation_id": eval_id,
        "session_id": sess.id,
        "goal": goal_text,
        "score": score,
        "feedback": feedback,
        "recommendations": recs,
        "status": status,
    }

