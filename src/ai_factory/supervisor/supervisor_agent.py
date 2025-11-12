from __future__ import annotations

import json
import uuid
from typing import Any, Dict, List

from ai_factory.services import supervisor_service as svc
from ai_factory.supervisor.supervisor_store import save_session
from ai_factory.memory.memory_embeddings import add_to_memory


def run_supervisor(goal: str) -> Dict[str, Any]:
    req_id = str(uuid.uuid4())

    plan = svc.generate_plan(goal)
    context_docs = svc.fetch_context(goal, n=3)

    step_results: List[Dict[str, Any]] = []
    for step in plan.get("steps", []):
        r = svc.maybe_run_code(step)
        step_results.append(r)

    result_text = svc.aggregate_result(step_results)
    status = svc.status_from(step_results)

    # Index a summary into vector memory for recall
    to_index = f"SUPERVISOR\nGOAL:\n{goal}\nPLAN_STEPS:{len(plan.get('steps',[]))}\nRESULT:\n{result_text}\nSTATUS:{status}"
    add_to_memory(req_id, to_index)

    plan_json = json.dumps(plan, ensure_ascii=False)
    context_text = "\n---\n".join(context_docs)
    save_session(req_id, goal, plan_json, context_text, result_text, status)

    return {
        "request_id": req_id,
        "goal": goal,
        "plan": plan,
        "context": context_docs,
        "result": result_text,
        "status": status,
    }

