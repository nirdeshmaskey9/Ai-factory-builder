from __future__ import annotations

import json
import time
import os
import subprocess
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request

from ai_factory.compat.v1_adapter import to_v2
from ai_factory.core.domain_detector import DomainDetector
from ai_factory.template_bank import TemplateRegistry, create_env
from ai_factory.builders.web.builder import WebBuilder
from ai_factory.builders.cli.builder import CliBuilder
from ai_factory.builders.ml.builder import MlBuilder
from ai_factory.evaluator.runner import EvaluationRunner


router = APIRouter(tags=["factory"])


def _log_master(decision: Dict[str, Any]) -> None:
    Path("deployments").mkdir(exist_ok=True)
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    p = Path(f"deployments/factory_master_log_{ts}.md")
    payload = json.dumps(decision, ensure_ascii=False, indent=2)
    content = (
        f"# Factory Master Log {ts}\n\n"
        f"- decision_time: {ts}\n"
        f"- outcome: {decision.get('outcome', 'unknown')}\n\n"
        f"```json\n{payload}\n```\n"
    )
    p.write_text(content, encoding="utf-8")


@router.post("/factory/create")
async def factory_create(request: Request):
    """Create a new build by detecting domain, selecting builder, evaluating, and logging.

    Body:
        {
          "blueprint": {...},
          "options": {...},
          "metadata": {...}
        }
    """
    # Parse raw JSON body (supports JSON string or JSON object)
    try:
        payload: Any = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Normalize payload into a dict blueprint/options/metadata
    blueprint: Dict[str, Any] = {}
    options: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}

    if isinstance(payload, str):
        # Plain string: treat as goal/description
        blueprint = {
            "name": "app",
            "title": "app",
            "description": payload,
            "goal": payload,
        }
    elif isinstance(payload, dict):
        blueprint = payload.get("blueprint") or {}
        options = payload.get("options") or payload.get("settings") or {}
        metadata = payload.get("metadata") or {}
        # Accept simplified payloads and top-level hints
        if not blueprint:
            if any(k in payload for k in ("goal", "title", "description", "name")):
                blueprint = {
                    "name": payload.get("name") or payload.get("title") or "app",
                    "title": payload.get("title") or payload.get("name") or "app",
                    "description": payload.get("description") or payload.get("goal") or "",
                    "goal": payload.get("goal", ""),
                }
        if not metadata and "domain" in payload:
            metadata = {"domain": str(payload.get("domain")).lower()}
    else:
        raise HTTPException(status_code=400, detail="Unsupported payload type. Use JSON object or JSON string.")

    # 1) Adapt to v2
    bp = to_v2(blueprint)

    # 2) Detect domain
    domain = DomainDetector.detect(bp, metadata)

    # Fill defaults for name/title based on domain if missing
    domain_defaults = {
        "web": "hello_web",
        "cli": "cli_app",
        "ml": "ml_project",
        "data": "data_project",
        "automation": "automation_project",
        "desktop": "desktop_app",
    }
    if not bp.get("name"):
        bp["name"] = domain_defaults.get(domain, "app")
    if not bp.get("title"):
        bp["title"] = bp["name"]

    # 3) Create builder
    registry = TemplateRegistry()
    template_root = registry.get_path(domain)
    try:
        env = create_env(template_root)
    except RuntimeError as e:
        # Surface missing Jinja2 or loader issues clearly
        raise HTTPException(status_code=500, detail=f"Template environment error: {e}")
    # Import stub builders for additional domains
    from ai_factory.builders.data.builder import DataBuilder
    from ai_factory.builders.automation.builder import AutomationBuilder
    from ai_factory.builders.desktop.builder import DesktopBuilder

    builder_map = {
        "web": WebBuilder(env),
        "cli": CliBuilder(env),
        "ml": MlBuilder(env),
        "data": DataBuilder(env),
        "automation": AutomationBuilder(env),
        "desktop": DesktopBuilder(env),
    }
    builder = builder_map.get(domain)

    # 4) Build
    try:
        result = builder.build(bp, options, ctx={"metadata": metadata})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Build failed: {e}")

    # 5) Evaluate
    try:
        eval_runner = EvaluationRunner()
        eval_report = await eval_runner.run(result.build_id, domain)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {e}")

    # Persist evaluation in DB and augment manifest
    try:
        from ai_factory.memory.memory_db import store_evaluation
        store_evaluation(result.build_id, domain, eval_report.passed, eval_report.summary, eval_report.artifacts)
    except Exception:
        pass
    try:
        # Update manifest with evaluation block
        manifest_path = Path(result.manifest_path)
        data = {}
        if manifest_path.exists():
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
        data["evaluation"] = {
            "passed": eval_report.passed,
            "summary": eval_report.summary,
            "artifacts": eval_report.artifacts,
        }
        tmp = manifest_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(manifest_path)
    except Exception:
        pass

    # 6) Log ADR-style entry
    decision = {
        "action": "factory_create",
        "outcome": "success" if eval_report.passed else "warning",
        "domain": domain,
        "build_id": result.build_id,
        "manifest": result.manifest_path,
        "summary": eval_report.summary,
    }
    _log_master(decision)

    # Try to open build folder in Explorer on Windows (skip during pytest)
    try:
        if eval_report.passed and os.name == "nt" and os.environ.get("PYTEST_CURRENT_TEST") is None:
            abs_out = os.path.abspath(result.outputs_path)
            subprocess.Popen(["explorer", abs_out])
    except Exception as e:
        print(f"[warn] could not open build folder: {e}")

    # Print color-coded success/summary banner
    try:
        from colorama import Fore, Style  # type: ignore
        green = Fore.GREEN
        reset = Style.RESET_ALL
    except Exception:
        green = reset = ""
    status_word = "SUCCESS" if eval_report.passed else "DONE"
    print(f"{green}🟢 {status_word}: {domain.upper()} build {result.build_id} at {result.outputs_path}{reset}")

    # 7) Response
    return {
        "build_id": result.build_id,
        "domain": domain,
        "manifest": result.manifest_path,
        "outputs_path": result.outputs_path,
        "evaluation": {
            "passed": eval_report.passed,
            "summary": eval_report.summary,
            "artifacts": eval_report.artifacts,
        },
    }
