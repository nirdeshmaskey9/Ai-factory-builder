from __future__ import annotations

from fastapi import APIRouter, Query
from typing import Any, Dict, List, Optional
from pathlib import Path
import os
import json
import time

from ai_factory.orchestrator.orchestrator_store import list_runs


router = APIRouter(prefix="/analytics", tags=["Analytics"])


def _dir_size_mb(path: Path) -> float:
    total = 0
    if not path.exists():
        return 0.0
    for root, _, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except Exception:
                pass
    return round(total / (1024 * 1024), 2)


def _read_run_duration(run_id: int) -> Optional[float]:
    try:
        p = Path("logs") / "orchestrator" / f"run_{run_id}.json"
        if not p.exists():
            return None
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return float(data.get("duration_sec")) if data.get("duration_sec") is not None else None
    except Exception:
        return None


def _template_usage() -> Dict[str, int]:
    root = Path("builds")
    usage: Dict[str, int] = {}
    if not root.exists():
        return usage
    for b in root.iterdir():
        if not b.is_dir():
            continue
        manifest = b / "manifest.json"
        tname: Optional[str] = None
        if manifest.exists():
            try:
                with manifest.open("r", encoding="utf-8") as f:
                    m = json.load(f)
                tname = m.get("template") or m.get("template_name")
            except Exception:
                tname = None
        if tname:
            usage[tname] = usage.get(tname, 0) + 1
    return usage


@router.get("/stats")
def stats() -> Dict[str, Any]:
    runs = list_runs(limit=1000, sort="desc")
    total = len(runs)
    status_counts = {"success": 0, "failed": 0, "deployed": 0, "partial": 0}
    durations: List[float] = []
    last_ts: Optional[str] = None
    for r in runs:
        if r.status in status_counts:
            status_counts[r.status] += 1
        dur = _read_run_duration(r.id)
        if dur is not None:
            durations.append(dur)
        if not last_ts and r.timestamp:
            last_ts = r.timestamp.isoformat()
    avg_duration = round(sum(durations) / len(durations), 2) if durations else 0.0
    success = status_counts.get("success", 0) + status_counts.get("deployed", 0)
    failed = status_counts.get("failed", 0)
    deployed = status_counts.get("deployed", 0)
    success_rate = round((success / total), 3) if total else 0.0

    logs_size = _dir_size_mb(Path("logs"))
    builds_count = len([p for p in Path("builds").iterdir() if p.is_dir()]) if Path("builds").exists() else 0

    return {
        "total_runs": total,
        "success": success,
        "failed": failed,
        "deployed": deployed,
        "success_rate": success_rate,
        "avg_duration": avg_duration,
        "templates_usage": _template_usage(),
        "last_run_time": last_ts,
        "log_dir_size_mb": logs_size,
        "builds_count": builds_count,
    }


@router.get("/trends")
def trends(limit: int = Query(20, ge=1, le=200)) -> List[Dict[str, Any]]:
    rows = list_runs(limit=limit, sort="desc")
    out: List[Dict[str, Any]] = []
    for r in rows:
        out.append({
            "run_id": r.id,
            "goal": r.goal,
            "status": r.status,
            "score": r.evaluation_score,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            "duration": _read_run_duration(r.id),
        })
    return out


@router.get("/system")
def system_info() -> Dict[str, Any]:
    try:
        import psutil  # type: ignore
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage(os.getcwd()).percent
        proc = psutil.Process(os.getpid())
        uptime = time.time() - proc.create_time()
        ok = True
    except Exception:
        cpu = mem = disk = uptime = 0.0
        ok = False
    # DB sizes
    def fsize(p: Path) -> int:
        try:
            return p.stat().st_size
        except Exception:
            return 0
    memdb = Path("ai_factory") / "data" / "memory.db"
    fbdb = Path("data") / "feedback.db"
    return {
        "available": ok,
        "cpu_percent": cpu,
        "memory_percent": mem,
        "disk_percent": disk,
        "uptime_sec": round(uptime, 2),
        "db_sizes": {
            "memory.db": fsize(memdb),
            "feedback.db": fsize(fbdb),
        },
        "version": os.getenv("FACTORY_VERSION", "v2.4-control-center"),
    }

