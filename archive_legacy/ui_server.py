"""AI Factory Mini UI (Phase 12.5)

Run: python ui_server.py
Launches a small FastAPI UI on http://127.0.0.1:8080 that lets you enter a goal,
select a domain, submit to the Factory (/factory/create on 8015), and view JSON results.
Also lists the 5 most recent builds with links to their folders and manifests.
"""

from __future__ import annotations

import json
import os
import webbrowser
from pathlib import Path

import httpx
import requests
import threading
import time
from scripts.factory_autocheck import ensure_backend_running
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn


app = FastAPI(title="AI Factory - Mini UI")
templates = Jinja2Templates(directory="ui_templates")

# Heartbeat to monitor backend availability
FACTORY_URL = "http://127.0.0.1:8015/factory/info"
factory_status = {"online": False}


def _heartbeat():
    while True:
        try:
            requests.get(FACTORY_URL, timeout=2)
            factory_status["online"] = True
        except Exception:
            factory_status["online"] = False
        time.sleep(3)


# Attempt to ensure backend is running on load
try:
    ensure_backend_running()
except Exception:
    pass

threading.Thread(target=_heartbeat, daemon=True).start()


def get_recent_builds(limit: int = 5):
    builds_dir = Path("builds")
    if not builds_dir.exists():
        return []
    builds = sorted(
        [b for b in builds_dir.iterdir() if b.is_dir()],
        key=lambda x: x.stat().st_mtime,
        reverse=True,
    )[:limit]
    results = []
    for b in builds:
        manifest = b / "manifest.json"
        results.append(
            {
                "id": b.name,
                "path": str(b.resolve()),
                "manifest": str(manifest.resolve()) if manifest.exists() else None,
            }
        )
    return results


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    builds = get_recent_builds()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "builds": builds, "factory_online": factory_status["online"]},
    )


@app.post("/submit", response_class=HTMLResponse)
async def submit(
    request: Request,
    goal: str = Form(...),
    domain: str = Form("web"),
    dynamic: str | None = Form(None),
):
    payload: dict = {"goal": goal, "domain": domain}
    if dynamic:
        payload["dynamic"] = True
    try:
        # If offline, try to start backend and warn user
        if not factory_status["online"]:
            ensure_backend_running()
            # recheck quickly
            try:
                requests.get(FACTORY_URL, timeout=3)
                factory_status["online"] = True
            except Exception:
                factory_status["online"] = False
        if not factory_status["online"]:
            data = {"error": "⚠️ The Factory backend isn’t running on port 8015. Please start it first."}
        else:
            with httpx.Client(timeout=120.0) as client:
                response = client.post("http://127.0.0.1:8015/factory/create", json=payload)
                data = response.json()
                # If dynamic web build, start local preview
                if payload.get("dynamic") and domain == "web" and isinstance(data, dict) and data.get("build_id"):
                    prev = client.get(f"http://127.0.0.1:8015/deployer/preview/{data['build_id']}")
                    if prev.status_code == 200:
                        data["preview_url"] = prev.json().get("preview_url")
    except Exception as e:
        data = {"error": str(e)}
    builds = get_recent_builds()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "result": data,
            "result_json": json.dumps(data, ensure_ascii=False, indent=2),
            "builds": builds,
            "factory_online": factory_status["online"],
        },
    )


@app.get("/restart_factory")
async def restart_factory():
    try:
        ensure_backend_running()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


if __name__ == "__main__":
    try:
        webbrowser.open("http://127.0.0.1:8080")
    except Exception:
        pass
    uvicorn.run(app, host="127.0.0.1", port=8080)
