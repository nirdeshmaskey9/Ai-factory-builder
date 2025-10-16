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


def package_app(goal: str, session_id: Optional[int], dest: Optional[Path] = None) -> Path:
    """Create a minimal FastAPI app package in dest directory.

    If dest is None, creates a temporary directory. Ensures the following exist:
      - app.py with /hello and root endpoints
      - main.py entrypoint to run uvicorn programmatically
      - requirements.txt with minimal deps
    """
    base = dest if dest is not None else Path(tempfile.mkdtemp(prefix="aifactory_deploy_"))
    base.mkdir(parents=True, exist_ok=True)

    app_py = base / "app.py"
    if not app_py.exists():
        app_code = (
            "from fastapi import FastAPI\n\n"
            "app = FastAPI()\n\n"
            "@app.get('/hello')\n"
            "def read_root():\n"
            "    return {'message': 'Factory Online'}\n\n"
            "@app.get('/')\n"
            "def index():\n"
            "    return {'message': 'App deployed successfully'}\n"
        )
        app_py.write_text(app_code, encoding="utf-8")

    main_py = base / "main.py"
    # Write a robust entrypoint that works regardless of launch CWD
    main_code = (
        "import os\n"
        "import sys\n"
        "from pathlib import Path\n"
        "import uvicorn\n\n"
        "if __name__ == \"__main__\":\n"
        "    # Ensure FastAPI app can always be found no matter where this is launched\n"
        "    sys.path.append(str(Path(__file__).parent))\n"
        "    port = int(os.getenv(\"PORT\", \"8000\"))\n"
        "    uvicorn.run(\"app:app\", host=\"127.0.0.1\", port=port)\n"
    )
    main_py.write_text(main_code, encoding="utf-8")

    req_txt = base / "requirements.txt"
    req_txt.write_text("fastapi\nuvicorn\n", encoding="utf-8")

    try:
        print(f"📦 Deployment packaged at: {base}")
    except Exception:
        print(f"[deploy] Deployment packaged at: {base}")
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
