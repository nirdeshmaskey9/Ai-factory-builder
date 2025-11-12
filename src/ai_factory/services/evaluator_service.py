from __future__ import annotations

import json
from typing import Tuple


def _coverage_score(goal: str, plan_json: str, result_text: str) -> float:
    goal_l = (goal or "").lower()
    in_plan = plan_json.lower().count(goal_l[: max(4, min(16, len(goal_l)))]) > 0 if goal_l else False
    in_result = goal_l and (goal_l.split(" ")[0] in result_text.lower())
    score = 0.5 * float(in_plan) + 0.5 * float(bool(in_result))
    return score


def _signal_score(result_text: str) -> float:
    # Reward some stdout, penalize long stderr/tracebacks
    rt = result_text or ""
    has_trace = ("traceback" in rt.lower()) or ("error" in rt.lower())
    length = len(rt)
    if has_trace:
        return 0.1
    if length == 0:
        return 0.2
    # cap effect
    return min(1.0, 0.2 + min(0.8, length / 200.0))


def compute_score(goal: str, plan_json: str, context_text: str, result_text: str) -> float:
    """Return a normalized score [0,1] using simple heuristics."""
    s1 = _coverage_score(goal, plan_json, result_text)
    s2 = _signal_score(result_text)
    return max(0.0, min(1.0, 0.5 * s1 + 0.5 * s2))


def derive_status(score: float) -> str:
    if score >= 0.75:
        return "pass"
    if score >= 0.4:
        return "improve"
    return "fail"


def summarize_feedback(goal: str, plan_json: str, context_text: str, result_text: str, score: float) -> Tuple[str, str]:
    plan_obj = {}
    try:
        plan_obj = json.loads(plan_json)
    except Exception:
        pass
    steps = len(plan_obj.get("steps", [])) if isinstance(plan_obj, dict) else 0
    feedback = (
        f"Evaluation for goal: '{goal}'. Steps={steps}. Score={score:.2f}. "
        f"Result length={len(result_text or '')}."
    )
    if score < 0.4:
        feedback += " Observed low signal or errors; recommend tightening steps and rerunning."
    elif score < 0.75:
        feedback += " Adequate output; consider refining prompts or adding tests."
    else:
        feedback += " Strong result; consider snapshotting or promoting artifacts."

    recs = "- Add explicit tests for key steps\n- Improve prompts for clarity\n- Re-run with smaller, verifiable increments"
    return feedback, recs


def make_memory_snippet(evaluation_id: int, session_id: int, goal: str, score: float, feedback: str, recommendations: str) -> str:
    return (
        "[EVALUATION v5]\n"
        f"evaluation_id: {evaluation_id}  session_id: {session_id}\n"
        f"goal: \"{goal}\"\n"
        f"score: {score:.2f}\n"
        f"feedback: {feedback}\n"
        f"recommendations: {recommendations}"
    )

