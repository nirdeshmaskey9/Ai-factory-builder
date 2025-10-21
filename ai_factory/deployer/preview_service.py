from __future__ import annotations

import atexit
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Dict
try:
    import psutil  # type: ignore
except Exception:
    psutil = None  # type: ignore


PREVIEW_PROCESSES: Dict[str, subprocess.Popen] = {}
PREVIEW_PORTS: Dict[str, int] = {}
ACTIVE_PREVIEWS: Dict[str, int] = PREVIEW_PORTS
launch_lock = threading.Semaphore(3)  # max 3 previews at once
guardian_running: bool = False
guardian_thread: threading.Thread | None = None
active_previews: Dict[str, dict] = {}


def _launch_preview(app_path: Path, port: int) -> subprocess.Popen:
    with launch_lock:
        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", f"{app_path.stem}:app", "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"],
            cwd=str(app_path.parent),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # give server a moment to start
        time.sleep(3)
        return proc


def _find_free_port(start: int = 9050, end: int = 9999) -> int:
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError("No free ports available")


def _guardian_loop() -> None:
    """Background loop to kill orphaned uvicorn processes left from crashed sessions."""
    global guardian_running
    while guardian_running:
        try:
            # Iterate over a copy to allow removal
            for build_id, info in list(active_previews.items()):
                pid = info.get("pid")
                started = info.get("start", time.time())
                if psutil is None:
                    continue
                if not psutil.pid_exists(pid):
                    print(f"[Guardian] Removing dead preview {build_id} (pid {pid})")
                    active_previews.pop(build_id, None)
                    continue
                try:
                    proc = psutil.Process(pid)
                    if time.time() - started > 3600:
                        print(f"[Guardian] Killing stale preview {build_id} after 1h uptime")
                        proc.kill()
                        active_previews.pop(build_id, None)
                except Exception:
                    pass
        except Exception as e:
            print(f"[Guardian] Error: {e}")
        time.sleep(30)


def start_guardian() -> None:
    global guardian_running, guardian_thread
    if not guardian_running:
        guardian_running = True
        guardian_thread = threading.Thread(target=_guardian_loop, daemon=True)
        guardian_thread.start()
        print("Preview Guardian started.")


def stop_guardian() -> None:
    global guardian_running
    guardian_running = False
    print("Preview Guardian stopped.")


def run_preview(build_id: str) -> dict:
    outputs_dir = Path("builds") / build_id / "outputs"
    # if app.py is under a named folder, pick the first directory
    app_dir = outputs_dir
    if outputs_dir.exists() and not (outputs_dir / "app.py").exists():
        subdirs = [p for p in outputs_dir.iterdir() if p.is_dir()]
        if subdirs:
            app_dir = subdirs[0]
    app_path = app_dir / "app.py"
    if not (app_path.exists() and app_path.is_file()):
        return {"detail": f"No app.py found in {outputs_dir}"}

    port = _find_free_port()
    proc = _launch_preview(app_path, port)
    PREVIEW_PROCESSES[build_id] = proc
    PREVIEW_PORTS[build_id] = port
    active_previews[build_id] = {"pid": proc.pid, "port": port, "start": time.time()}
    start_guardian()
    atexit.register(lambda: proc.terminate())
    return {"preview_url": f"http://127.0.0.1:{port}/hello", "pid": proc.pid}


def stop_preview(build_id: str) -> dict:
    proc = PREVIEW_PROCESSES.pop(build_id, None)
    PREVIEW_PORTS.pop(build_id, None)
    if proc:
        proc.terminate()
        return {"stopped": True}
    return {"stopped": False}


def stop_all_previews() -> dict:
    if not PREVIEW_PROCESSES:
        return {"detail": "No active previews"}
    for k, p in list(PREVIEW_PROCESSES.items()):
        try:
            p.terminate()
        finally:
            PREVIEW_PROCESSES.pop(k, None)
            PREVIEW_PORTS.pop(k, None)
            active_previews.pop(k, None)
    return {"stopped_all": True}


def list_active_previews() -> list[dict]:
    out = []
    for bid, proc in PREVIEW_PROCESSES.items():
        port = PREVIEW_PORTS.get(bid)
        out.append({"build_id": bid, "pid": getattr(proc, "pid", None), "port": port})
    return out
