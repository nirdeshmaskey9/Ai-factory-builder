from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter

from ai_factory.memory.memory_db import get_session
from ai_factory.deployer.preview_service import list_active_previews
from ai_factory.deployer.deployer_store import get_recent


router = APIRouter(tags=["system-health"])


def _factory_info() -> dict[str, Any]:
    # Mimic /factory/info without importing main to avoid circular imports
    try:
        rows = get_recent(limit=100)
        running = sum(1 for r in rows if str(getattr(r, 'status', '')).lower() == 'running')
    except Exception:
        running = 0
    try:
        version = Path("VERSION").read_text(encoding="utf-8").strip()
    except Exception:
        version = "unknown"
    return {"version": version, "running_deployments": running, "healthy": True}


@router.get("/system/health/full")
def full_health_check():
    """Performs deep system diagnostics and returns status of all subsystems."""
    summary: dict[str, Any] = {}
    # Core folders
    summary["routes_ok"] = all([
        os.path.exists("builds"),
        os.path.exists("deployments"),
        os.path.exists("logs"),
    ])
    # DB check
    try:
        sess = get_session()
        list(sess.execute("SELECT 1"))
        try:
            sess.close()
        except Exception:
            pass
        summary["db_ok"] = True
    except Exception as e:
        summary["db_ok"] = False
        summary["db_error"] = str(e)
    # Processes
    procs = []
    try:
        import psutil  # type: ignore
        procs = [p.info for p in psutil.process_iter(['pid', 'name']) if (p.info.get('name') or '').lower().find('uvicorn') >= 0]
    except Exception:
        pass
    summary["processes_alive"] = procs
    try:
        import psutil  # type: ignore
        summary["disk_usage"] = psutil.disk_usage(".")._asdict()
    except Exception:
        try:
            import shutil
            du = shutil.disk_usage(".")
            summary["disk_usage"] = {"total": du.total, "used": du.used, "free": du.free}
        except Exception:
            summary["disk_usage"] = {}
    # Factory meta
    summary["factory_info"] = _factory_info()
    # Previews
    try:
        summary["active_previews"] = list_active_previews()
    except Exception:
        summary["active_previews"] = []
    status = "healthy" if summary.get("db_ok") else "degraded"
    return {"status": status, "summary": summary}
