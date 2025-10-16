from __future__ import annotations

import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

_REGISTRY: dict[int, subprocess.Popen] = {}


def find_free_port(start: int = 8001) -> int:
    port = start
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                port += 1


def package_app(goal: str, session_id: Optional[int]) -> Path:
    base = Path(tempfile.mkdtemp(prefix="aifactory_deploy_"))
    app_py = base / "app.py"
    app_code = (
        "from fastapi import FastAPI\n"
        "app = FastAPI(title='Deployed App', version='1.0.0')\n\n"
        f"GOAL = {goal!r}\n"
        "@app.get('/health')\n"
        "def health():\n"
        "    return {'status':'ok','goal':GOAL}\n"
    )
    app_py.write_text(app_code, encoding="utf-8")
    return base


def launch_app(path: Path, port: int) -> subprocess.Popen:
    env = os.environ.copy()
    cmd = [sys.executable, "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"]
    proc = subprocess.Popen(cmd, cwd=str(path), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    # Give server a brief moment to start
    time.sleep(0.5)
    return proc


def check_status(proc: subprocess.Popen) -> str:
    return "running" if proc.poll() is None else "stopped"


def register_process(deployment_id: int, proc: subprocess.Popen) -> None:
    _REGISTRY[deployment_id] = proc


def get_process(deployment_id: int) -> Optional[subprocess.Popen]:
    return _REGISTRY.get(deployment_id)


def stop_process(deployment_id: int) -> None:
    proc = _REGISTRY.get(deployment_id)
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()
    _REGISTRY.pop(deployment_id, None)


def make_memory_snippet(goal: str, port: int, version: str, status: str) -> str:
    return (
        "[DEPLOY v7]\n"
        f"goal: {goal}\n"
        f"endpoint: http://127.0.0.1:{port}\n"
        f"version: {version}\n"
        f"status: {status}"
    )

