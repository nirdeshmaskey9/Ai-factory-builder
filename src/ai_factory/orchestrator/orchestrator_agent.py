from __future__ import annotations

import json
import uuid
from typing import Any, Dict, Optional
import time
import os

from ai_factory.services.supervisor_service import generate_plan, fetch_context
from ai_factory.services.router_v2_service import route as router_decide
from ai_factory.supervisor.supervisor_agent import run_supervisor
from ai_factory.evaluator.evaluator_agent import evaluate as eval_session
from ai_factory.builder.builder_agent import rebuild
from ai_factory.deployer.deployer_agent import deploy as deploy_app
from ai_factory.supervisor.supervisor_store import get_recent as supervisor_recent

from ai_factory.orchestrator.orchestrator_store import create_run, update_run, get_run, get_recent, log_step
from ai_factory.services.orchestrator_service import (
    choose_primary_task_type,
    success_threshold,
    max_attempts_or_default,
    should_repair,
    make_orch_snippet,
)
from ai_factory.memory.memory_embeddings import add_to_memory


def run(goal: str, max_attempts: Optional[int] = None, deploy: bool = False) -> Dict[str, Any]:
    t0 = time.time()
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
    # Optional: pull RAG context before planning (Phase 4.0)
    try:
        from ai_factory import config_runtime_flags as _r
        if _r.rag_enabled and goal:
            try:
                from ai_factory.rag import rag_service as _rag
                rag_ctx = _rag.retrieve(goal, top_k=3)
            except Exception:
                rag_ctx = []
        else:
            rag_ctx = []
    except Exception:
        rag_ctx = []

    plan = generate_plan(goal)
    plan_json = json.dumps(plan, ensure_ascii=False)
    task_type = choose_primary_task_type(plan_json)
    route_dec = router_decide(task_type)
    chosen_model = route_dec.get("model_name", chosen_model)
    context_docs = fetch_context(goal, n=3)
    try:
        rag_texts = [x.get("text", "") for x in rag_ctx][:3]
    except Exception:
        rag_texts = []
    context_text = "\n---\n".join(context_docs + rag_texts)

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

    # Advisor decision at start (non-fatal); log to memory
    advisor_decision = None
    try:
        from ai_factory.advisor.advisor_service import route_task as advisor_route
        advisor_decision = advisor_route(goal, domain="code", hint=None, topk=3)
        try:
            from ai_factory.memory.memory_agent import store_memory as _store
            _store(None, goal=f"Advisor decision (run {run_id})", summary=f"{advisor_decision.get('backend')}/{advisor_decision.get('model')} ({advisor_decision.get('role')})", tags=["advisor_decision", str(advisor_decision.get('role'))], score=None)
        except Exception:
            pass
    except Exception:
        advisor_decision = None

    # Ensure log directories
    try:
        os.makedirs(os.path.join("logs", "orchestrator"), exist_ok=True)
        os.makedirs(os.path.join("logs", "supervisor"), exist_ok=True)
    except Exception:
        pass

    # Log planning step
    try:
        plan_path = os.path.join("logs", "orchestrator", f"plan_{run_id}.json")
        with open(plan_path, "w", encoding="utf-8") as f:
            f.write(plan_json)
        log_step(run_id, "plan", "ok", plan_path)
    except Exception:
        log_step(run_id, "plan", "ok")

    # Auto-pass for system goals
    sys_markers = ["audit", "health", "system check", "status", "self-verify"]
    if any(m in (g or "").lower() for m in sys_markers for g in [goal]):
        update_run(
            run_id,
            attempt=1,
            status="success",
            debugger_stdout=dbg_out,
            debugger_stderr=dbg_err,
            evaluation_score=0.0,
            notes="Auto-pass system goal",
        )
        snippet = make_orch_snippet(goal, chosen_model, 0.0, "success", None)
        add_to_memory(f"orch:{req_id}", snippet)
        duration = time.time() - t0
        report_path = os.path.join("logs", "orchestrator", f"run_{run_id}.json")
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump({
                    "run_id": run_id,
                    "status": "success",
                    "tasks_completed": 0,
                    "attempts": 1,
                    "duration_sec": duration,
                    "report_path": report_path,
                }, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        return {
            "run_id": run_id,
            "request_id": req_id,
            "status": "success",
            "score": 0.0,
            "attempts": 1,
            "duration_sec": duration,
            "report_path": report_path,
            "deployment": None,
        }

    while attempts < max_att:
        attempts += 1
        # Execute (use supervisor to run steps; it will log a session)
        sup = run_supervisor(goal)
        # Persist supervisor report for this run_id for traceability
        try:
            sup_path = os.path.join("logs", "supervisor", f"report_{run_id}.json")
            with open(sup_path, "w", encoding="utf-8") as f:
                json.dump(sup, f, ensure_ascii=False, indent=2)
            log_step(run_id, f"supervisor_attempt_{attempts}", "ok", sup_path)
        except Exception:
            log_step(run_id, f"supervisor_attempt_{attempts}", "ok")
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
            log_step(run_id, f"decision_attempt_{attempts}", status)
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
            log_step(run_id, f"repair_attempt_{attempts}", "retry")
            # Exponential backoff: 1s, 2s, 4s
            try:
                time.sleep(min(4, 2 ** (attempts - 1)))
            except Exception:
                pass
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
        log_step(run_id, f"decision_attempt_{attempts}", status)
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

    # Auto-learn into Memory on successful outcome
    try:
        if status in ("success", "deployed"):
            from ai_factory.memory.memory_agent import auto_learn_from_run
            auto_learn_from_run(run_id=run_id, goal=goal, summary=dbg_out or goal, tags=["orchestrator","autolearn"])
            try:
                log_step(run_id, "memory_autolearn", "ok")
                # Also append a friendly note into run report file
                report_path = os.path.join("logs", "orchestrator", f"run_{run_id}.json")
                if os.path.exists(report_path):
                    import json as _json
                    with open(report_path, "r", encoding="utf-8") as f:
                        _j = _json.load(f)
                    _j["memory_autolearned"] = True
                    _j["note"] = f"\ud83e\udde0 Memory auto-learned from run {run_id}"
                    with open(report_path, "w", encoding="utf-8") as f:
                        _json.dump(_j, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
    except Exception:
        pass

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

    duration = time.time() - t0
    # Write a consolidated run report
    report = {
        "run_id": run_id,
        "status": status,
        "tasks_completed": 0,
        "attempts": attempts,
        "duration_sec": duration,
        "advisor_decision": advisor_decision,
    }
    report_path = os.path.join("logs", "orchestrator", f"run_{run_id}.json")
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return {
        "run_id": run_id,
        "request_id": req_id,
        "status": status,
        "score": float(score if 'score' in locals() else 0.0),
        "attempts": attempts,
        "duration_sec": duration,
        "report_path": report_path,
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
