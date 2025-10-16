from __future__ import annotations

import json
import uuid
from typing import Any, Dict, Optional

from ai_factory.services.supervisor_service import generate_plan, fetch_context
from ai_factory.services.router_v2_service import route as router_decide
from ai_factory.supervisor.supervisor_agent import run_supervisor
from ai_factory.evaluator.evaluator_agent import evaluate as eval_session
from ai_factory.builder.builder_agent import rebuild
from ai_factory.deployer.deployer_agent import deploy as deploy_app
from ai_factory.supervisor.supervisor_store import get_recent as supervisor_recent

from ai_factory.orchestrator.orchestrator_store import create_run, update_run, get_run, get_recent
from ai_factory.services.orchestrator_service import (
    choose_primary_task_type,
    success_threshold,
    max_attempts_or_default,
    should_repair,
    make_orch_snippet,
)
from ai_factory.memory.memory_embeddings import add_to_memory


def run(goal: str, max_attempts: Optional[int] = None, deploy: bool = False) -> Dict[str, Any]:
    req_id = str(uuid.uuid4())
    attempts = 0
    max_att = max_attempts_or_default(max_attempts)
    last_score = 0.0
    builder_rev_id: Optional[int] = None
    deployment_id: Optional[int] = None
    chosen_model = "gpt4"
    dbg_out = ""
    dbg_err = ""

    # Plan & route once per run (can be refined per attempt)
    plan = generate_plan(goal)
    plan_json = json.dumps(plan, ensure_ascii=False)
    task_type = choose_primary_task_type(plan_json)
    route_dec = router_decide(task_type)
    chosen_model = route_dec.get("model_name", chosen_model)
    context_docs = fetch_context(goal, n=3)
    context_text = "\n---\n".join(context_docs)

    status = "running"
    run_id = create_run(
        request_id=req_id,
        goal=goal,
        attempt=1,
        status=status,
        plan_json=plan_json,
        chosen_model=chosen_model,
        context_snippet=context_text,
        debugger_stdout=dbg_out,
        debugger_stderr=dbg_err,
        evaluation_score=0.0,
        builder_revision_id=None,
        deployment_id=None,
        notes="orchestrator started",
    )

    while attempts < max_att:
        attempts += 1
        # Execute (use supervisor to run steps; it will log a session)
        sup = run_supervisor(goal)
        # get latest supervisor session id
        sess_rows = supervisor_recent(limit=1)
        sess_id = sess_rows[0].id if sess_rows else -1
        # Evaluate
        ev = eval_session(session_id=sess_id)
        score = float(ev.get("score", 0.0))

        # Update debugging fields from supervisor output
        dbg_out = (sup.get("result") or "")
        dbg_err = ""

        # Decide
        if score >= success_threshold():
            status = "success"
            if deploy:
                dep = deploy_app(session_id=sess_id)
                deployment_id = dep.get("deployment_id")
                status = "deployed" if deployment_id else status
            update_run(
                run_id,
                attempt=attempts,
                status=status,
                debugger_stdout=dbg_out,
                debugger_stderr=dbg_err,
                evaluation_score=score,
                deployment_id=deployment_id,
                notes="orchestrator success",
            )
            break

        # Consider repair
        if should_repair(last_score, score, attempts, max_att):
            builder = rebuild(ev.get("evaluation_id"))
            builder_rev_id = builder.get("revision_id")
            last_score = score
            # Continue next attempt
            update_run(
                run_id,
                attempt=attempts,
                status="partial",
                debugger_stdout=dbg_out,
                debugger_stderr=dbg_err,
                evaluation_score=score,
                builder_revision_id=builder_rev_id,
                notes="attempt repair",
            )
            continue

        # No more attempts or unrecoverable
        update_run(
            run_id,
            attempt=attempts,
            status="failed",
            debugger_stdout=dbg_out,
            debugger_stderr=dbg_err,
            evaluation_score=score,
            notes="orchestrator failed",
        )
        status = "failed"
        break

    # Ensure deployment when requested, even if evaluation failed
    if deploy and not deployment_id:
        try:
            dep = deploy_app(goal=goal)
            deployment_id = dep.get("deployment_id")
            if deployment_id:
                status = "deployed"
                update_run(
                    run_id,
                    attempt=attempts,
                    status=status,
                    debugger_stdout=dbg_out,
                    debugger_stderr=dbg_err,
                    evaluation_score=float(score if 'score' in locals() else 0.0),
                    deployment_id=deployment_id,
                    notes="forced deploy",
                )
        except Exception:
            pass

    # Memory snippet
    endpoint = None
    if deployment_id:
        from ai_factory.deployer.deployer_store import get_deployment

        dep = get_deployment(deployment_id)
        endpoint = dep.endpoint if dep else None
    snippet = make_orch_snippet(goal, chosen_model, float(score if 'score' in locals() else 0.0), status, endpoint)
    add_to_memory(f"orch:{req_id}", snippet)

    # Additional adaptive evaluation memory tag (Phase 10.1)
    try:
        from ai_factory.services.evaluator_v2_service import get_average_reward
        thr = success_threshold()
        avg = float(get_average_reward())
        add_to_memory(
            f"orch-eval:{req_id}",
            f"[ORCH v10.1] Adaptive evaluation applied — score={float(score if 'score' in locals() else 0.0):.2f}, threshold={thr:.2f}, reward_avg={avg:.2f}",
        )
    except Exception:
        pass

    return {
        "run_id": run_id,
        "request_id": req_id,
        "status": status,
        "score": float(score if 'score' in locals() else 0.0),
        "attempts": attempts,
        "deployment": {"id": deployment_id, "endpoint": endpoint} if deployment_id else None,
    }


def status(run_id: int) -> Dict[str, Any]:
    r = get_run(run_id)
    if not r:
        return {}
    return {
        "run_id": r.id,
        "request_id": r.request_id,
        "goal": r.goal,
        "attempt": r.attempt,
        "status": r.status,
        "score": r.evaluation_score,
        "deployment_id": r.deployment_id,
        "timestamp": r.timestamp.isoformat() if r.timestamp else None,
    }


def history(limit: int = 10) -> Any:
    rows = get_recent(limit=limit)
    return [
        {
            "run_id": r.id,
            "goal": r.goal,
            "status": r.status,
            "score": r.evaluation_score,
            "attempt": r.attempt,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
        }
        for r in rows
    ]
