from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional


def _load_json(path: str) -> Optional[dict]:
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        return None
    return None


def _find_run_paths(run_id: int) -> Dict[str, Optional[str]]:
    # Prefer data logs, then fallback to root logs
    data_base = os.path.join("data", "app-internal", "logs")
    root_base = "logs"
    run_rel = os.path.join("orchestrator", f"run_{run_id}.json")
    sup_rel = os.path.join("supervisor", f"report_{run_id}.json")
    run_path = os.path.join(data_base, run_rel)
    sup_path = os.path.join(data_base, sup_rel)
    if not os.path.exists(run_path):
        run_path = os.path.join(root_base, run_rel)
    if not os.path.exists(sup_path):
        sup_path = os.path.join(root_base, sup_rel)
    return {"run": run_path if os.path.exists(run_path) else None, "sup": sup_path if os.path.exists(sup_path) else None}


def _derive_tags(goal: str, run: dict | None, sup: dict | None) -> List[str]:
    tags: List[str] = []
    base = (goal or "")
    for w in ["fastapi", "flask", "streamlit", "web", "cli", "ml", "api", "dashboard", "orchestrator", "evaluator", "planner"]:
        if w in base.lower():
            tags.append(w)
    # add by template/domain if present
    for src in (run, sup):
        if not isinstance(src, dict):
            continue
        for key in ("domain", "template", "templates", "status"):
            val = src.get(key)
            if isinstance(val, str):
                for tok in val.replace(",", " ").split():
                    t = tok.strip().lower()
                    if t and t not in tags and len(t) <= 24:
                        tags.append(t)
            elif isinstance(val, list):
                for tok in val:
                    t = str(tok).strip().lower()
                    if t and t not in tags and len(t) <= 24:
                        tags.append(t)
    # dedupe
    out: List[str] = []
    for t in tags:
        if t not in out:
            out.append(t)
    return out[:10]


def summarize_run(run_id: int) -> Dict[str, object]:
    paths = _find_run_paths(run_id)
    if not paths.get("run"):
        raise FileNotFoundError(f"orchestrator run JSON not found for id={run_id}")

    run = _load_json(paths["run"]) or {}
    sup = _load_json(paths.get("sup") or "") or {}

    goal = run.get("goal") or run.get("input_goal") or run.get("run", {}).get("goal") or ""
    status = run.get("status") or sup.get("status") or run.get("run", {}).get("status") or "unknown"
    result = run.get("result") or sup.get("result") or run.get("run", {}).get("result") or ""

    # Compact summary: goal → what happened → result
    steps = run.get("steps") or []
    step_names = ", ".join([str(s.get("step_name", s.get("name", "step"))) for s in steps][:5])
    summary = (
        f"Goal: {goal}. "
        + (f"Steps: {step_names}. " if step_names else "")
        + (f"Status: {status}. " if status else "")
        + (f"Result: {result}." if result else "")
    ).strip()
    if not summary:
        summary = f"Run {run_id}: No detailed logs found."

    # Tags and score
    tags = _derive_tags(goal, run, sup)
    score = None
    for k in ("evaluation_score", "score"):
        v = run.get(k) or sup.get(k)
        try:
            if v is not None:
                score = float(v)
                break
        except Exception:
            pass

    return {"summary": summary, "tags": tags, "score": score}

