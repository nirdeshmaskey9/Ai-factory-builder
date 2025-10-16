from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from ai_factory.services.planner_service import planner
from ai_factory.memory.memory_embeddings import semantic_search
from ai_factory.debugger.debugger_runner import run_code

logger = logging.getLogger(__name__)


def generate_plan(goal: str) -> Dict[str, Any]:
    """Use in-proc stub planner to produce a plan dict."""
    resp = planner.plan(goal, "general")
    # Convert pydantic model to plain dict
    return {
        "request_id": resp.request_id,
        "created_at": resp.created_at.isoformat(),
        "task_type": resp.task_type,
        "steps": [s.model_dump() for s in resp.steps],
        "estimated_tokens": resp.estimated_tokens,
        "model_name": resp.model_name,
        "notes": resp.notes,
    }


def fetch_context(goal: str, n: int = 3) -> List[str]:
    """Query vector memory for related snippets; return top document texts."""
    results = semantic_search(goal, n_results=n) or {}
    docs = results.get("documents", [[]])
    return docs[0] if docs else []


def maybe_run_code(step: Dict[str, Any]) -> Dict[str, Any]:
    """Heuristic: if a step suggests code, run a tiny Python snippet."""
    action = (step.get("action") or "").lower()
    if any(k in action for k in ("code", "python", "script")):
        snippet = f"print('Supervisor executing step:', {json.dumps(step.get('action',''))})"
        result = run_code(language="python", code=snippet, timeout=5)
        return result
    return {"stdout": "", "stderr": "", "exit_code": 0, "status": "skipped"}


def aggregate_result(step_results: List[Dict[str, Any]]) -> str:
    parts = []
    for i, r in enumerate(step_results):
        out = (r.get("stdout") or "").strip()
        err = (r.get("stderr") or "").strip()
        if out:
            parts.append(f"[step {i}] stdout:\n{out}")
        if err:
            parts.append(f"[step {i}] stderr:\n{err}")
    return "\n\n".join(parts) if parts else "no-op"


def status_from(results: List[Dict[str, Any]]) -> str:
    if not results:
        return "success"
    if any(r.get("status") == "error" for r in results):
        return "partial" if any(r.get("status") == "success" for r in results) else "error"
    return "success"

