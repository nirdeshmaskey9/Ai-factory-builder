from __future__ import annotations

import tempfile
import subprocess
import sys
import uuid
from typing import Dict, Any


def run_python(code: str, timeout: int = 5) -> Dict[str, Any]:
    """Execute Python code in a subprocess with a timeout, capturing stdout/stderr."""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(code)
        tmp_path = tmp.name

    try:
        proc = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "exit_code": proc.returncode,
            "status": "success" if proc.returncode == 0 else "error",
        }
    except subprocess.TimeoutExpired as te:
        return {"stdout": te.stdout or "", "stderr": (te.stderr or "") + "\nTimeoutExpired", "exit_code": 124, "status": "timeout"}


def run_code(language: str, code: str, timeout: int = 5) -> Dict[str, Any]:
    lang = (language or "").lower()
    if lang not in ("python", "py"):
        return {"stdout": "", "stderr": f"Unsupported language: {language}", "exit_code": 2, "status": "error"}
    return run_python(code, timeout=timeout)

