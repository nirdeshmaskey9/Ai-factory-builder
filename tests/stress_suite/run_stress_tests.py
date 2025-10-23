from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List

from fastapi.testclient import TestClient
import sys
sys.path.append(str(Path(__file__).resolve().parents[2]))


def _mk_client() -> TestClient:
    # Import the FastAPI app from the project
    from ai_factory.main import app  # type: ignore
    return TestClient(app)


def _log_line(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _tests_matrix() -> List[Dict[str, Any]]:
    return [
        {
            "category": "Simple Web App",
            "app_name": "Task Tracker",
            "domain": "web",
            "blueprint": {
                "name": "task_tracker",
                "title": "Task Tracker",
                "description": "FastAPI + SQLite + Jinja2 CRUD tasks with routes /, /add, /list",
                "goal": "Generate a simple task tracker with FastAPI and SQLite and Jinja2 with routes /, /add, /list",
            },
        },
        {
            "category": "CLI Tool",
            "app_name": "File Organizer CLI",
            "domain": "cli",
            "blueprint": {
                "name": "file_organizer_cli",
                "title": "File Organizer CLI",
                "description": "automation CLI tool to sort files by type into folders",
                "goal": "Create an automation CLI that organizes files by extension into subfolders",
            },
        },
        {
            "category": "ML Scaffold",
            "app_name": "Scatter Plot Generator",
            "domain": "ml",
            "blueprint": {
                "name": "scatter_plot_generator",
                "title": "Scatter Plot Generator",
                "description": "Generate a Matplotlib scatter plot saved as scatter.png",
                "goal": "Create a minimal ML scaffold notebook that saves a scatter plot",
            },
        },
        {
            "category": "Logic App",
            "app_name": "Reminder Scheduler",
            "domain": "web",
            "blueprint": {
                "name": "reminder_scheduler",
                "title": "Reminder Scheduler",
                "description": "FastAPI background task loop with APScheduler; routes /add, /list",
                "goal": "Create a reminder scheduler app with routes /add and /list and mention APScheduler",
            },
        },
        {
            "category": "Creative App",
            "app_name": "Prompt Writer",
            "domain": "web",
            "blueprint": {
                "name": "prompt_writer",
                "title": "Prompt Writer",
                "description": "Generate image prompts from keywords via /generate endpoint (image)",
                "goal": "Build a small image prompt generator with /generate route that accepts keywords",
            },
        },
        {
            "category": "Database App",
            "app_name": "Expense Tracker",
            "domain": "web",
            "blueprint": {
                "name": "expense_tracker",
                "title": "Expense Tracker",
                "description": "FastAPI CRUD entries in SQLite with totals view; routes /, /add, /summary",
                "goal": "Expense tracker with SQLite and summary totals at /summary",
            },
        },
        {
            "category": "Hybrid App",
            "app_name": "Notes + Tagging System",
            "domain": "web",
            "blueprint": {
                "name": "notes_tags",
                "title": "Notes + Tags",
                "description": "Multiple routes and multi-table relations; routes /, /notes, /tags",
                "goal": "Notes+Tags system with multiple routes and relations",
            },
        },
    ]


def run() -> int:
    client = _mk_client()
    log_file = Path("logs/stress_test.log")
    # Lazy import stress logger/utilities
    try:
        from ai_factory.evaluator.evaluator_main import (
            log_stress_result,  # type: ignore
            generate_stress_report,  # type: ignore
        )
    except Exception:
        log_stress_result = None  # type: ignore
        generate_stress_report = None  # type: ignore

    completed: List[Dict[str, Any]] = []
    for case in _tests_matrix():
        payload = {
            "blueprint": case["blueprint"],
            "metadata": {"domain": case["domain"]},
        }
        started = time.time()
        errors: List[str] = []
        try:
            resp = client.post("/factory/create", json=payload, timeout=120)
            if resp.status_code != 200:
                errors.append(f"HTTP {resp.status_code}")
                data: Dict[str, Any] = {"error": f"status {resp.status_code}"}
            else:
                data = resp.json()
        except Exception as e:
            errors.append(str(e))
            data = {"error": str(e)}
        elapsed = round(time.time() - started, 3)

        build_id = data.get("build_id")
        domain = data.get("domain", case["domain"])
        ev = data.get("evaluation") or {}
        passed = bool(ev.get("passed")) if isinstance(ev, dict) else False
        # Persist per-case result
        result_line = {
            "ts": int(time.time()),
            "category": case["category"],
            "app_name": case["app_name"],
            "build_id": build_id,
            "domain": domain,
            "passed": passed,
            "time_taken": elapsed,
            "errors": errors,
            "summary": (ev.get("summary") if isinstance(ev, dict) else None),
        }
        _log_line(log_file, result_line)
        if log_stress_result is not None:
            try:
                log_stress_result(
                    build_id=build_id or "",
                    domain=domain,
                    passed=passed,
                    time_taken=elapsed,
                    errors=errors,
                )
            except Exception:
                pass
        if not passed:
            print(f"[FAILURE] {case['category']} {case['app_name']} — {errors or ev}")
        else:
            print(f"[OK] {case['category']} {case['app_name']} in {elapsed}s")
        completed.append(result_line)

    # Generate summary
    if generate_stress_report is not None:
        try:
            generate_stress_report()
        except Exception:
            pass
    print("Stress suite completed.")
    return 0


if __name__ == "__main__":
    os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    raise SystemExit(run())
