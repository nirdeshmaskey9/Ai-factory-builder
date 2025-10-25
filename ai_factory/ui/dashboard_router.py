from __future__ import annotations

from fastapi import APIRouter, Request, HTTPException, Path
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from typing import List, Dict, Any
from pathlib import Path as PPath
import subprocess
import sys
import os
import json

from ai_factory.routers.factory_info import factory_info as get_factory_info
from ai_factory.orchestrator.orchestrator_store import list_runs, get_run_summary


templates = Jinja2Templates(directory="ai_factory/ui/templates")
router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _list_builds() -> List[Dict[str, Any]]:
    root = PPath("builds")
    if not root.exists():
        return []
    items: List[Dict[str, Any]] = []
    for bdir in sorted([p for p in root.iterdir() if p.is_dir()]):
        build_id = bdir.name
        created_at = None
        try:
            created_at = bdir.stat().st_mtime
        except Exception:
            pass
        # Find outputs subfolders
        outputs = bdir / "outputs"
        apps = []
        if outputs.exists():
            for sub in outputs.rglob("*"):
                if sub.is_dir():
                    apps.append(str(sub.relative_to(root)))
        items.append({
            "build_id": build_id,
            "created_at": created_at,
            "apps": apps,
        })
    return items


@router.get("")
@router.get("/")
def dashboard_index(request: Request):
    info = get_factory_info()
    builds = _list_builds()
    return templates.TemplateResponse("dashboard/index.html", {"request": request, "factory": info, "builds": builds})


@router.get("/runs")
def dashboard_runs(request: Request):
    # Query params
    q = request.query_params.get('q', '')
    status = request.query_params.get('status') or None
    sort = request.query_params.get('sort') or 'desc'
    limit = int(request.query_params.get('limit') or 20)

    runs = list_runs(limit=limit, sort=sort)
    view = []
    for r in runs:
        # Optionally read duration from report
        run_report_path = os.path.join("logs", "orchestrator", f"run_{r.id}.json")
        duration = None
        if os.path.exists(run_report_path):
            try:
                with open(run_report_path, "r", encoding="utf-8") as f:
                    j = json.load(f)
                    duration = j.get("duration_sec")
            except Exception:
                pass
        item = {
            "run_id": r.id,
            "goal": r.goal,
            "status": r.status,
            "score": r.evaluation_score,
            "attempt": r.attempt,
            "duration_sec": duration,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
        }
        view.append(item)

    # Filter
    if status:
        view = [x for x in view if x['status'] == status]
    if q:
        ql = q.lower()
        view = [x for x in view if ql in (x['goal'] or '').lower()]

    # Export
    dl = request.query_params.get('download')
    if dl == 'json':
        from fastapi.responses import JSONResponse
        return JSONResponse(view)
    if dl == 'csv':
        import io, csv
        from fastapi.responses import PlainTextResponse
        buf = io.StringIO()
        fieldnames = ["run_id","goal","status","score","duration_sec","timestamp"]
        w = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction='ignore')
        w.writeheader()
        for row in view:
            w.writerow({k: row.get(k) for k in fieldnames})
        return PlainTextResponse(buf.getvalue(), media_type='text/csv')

    return templates.TemplateResponse("dashboard/runs.html", {"request": request, "runs": view, "q": q, "status": status, "sort": sort, "limit": limit})


@router.get("/summary/{run_id}")
def dashboard_summary(request: Request, run_id: int = Path(..., ge=1)):
    summary = get_run_summary(run_id)
    if summary.get("not_found"):
        raise HTTPException(status_code=404, detail="run not found")
    pretty = json.dumps(summary, ensure_ascii=False, indent=2)
    return templates.TemplateResponse("dashboard/summary.html", {"request": request, "run_id": run_id, "summary": summary, "pretty": pretty})


@router.get("/analytics")
def dashboard_analytics(request: Request):
    return templates.TemplateResponse("dashboard/analytics.html", {"request": request})


@router.get("/launch/{build_id}")
def dashboard_launch(build_id: str = Path(...)):
    # Non-blocking spawn of the script
    script = PPath("scripts") / "run_app.py"
    if not script.exists():
        raise HTTPException(status_code=404, detail="launcher script not found")
    try:
        cmd = [sys.executable, str(script), "--id", str(build_id)]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return JSONResponse({"status": "launched", "build_id": build_id})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"launch failed: {e}")
