from __future__ import annotations

import os
from pathlib import Path
import time


def validate_env() -> None:
    """
    Parse .env-style variables and validate basic requirements. Non-fatal.

    - OPENAI_API_KEY present and length > 40
    - Ensure DB_PATH and DEPLOYMENTS_DIR exist (create if needed)
    - Log results to deployments/env_check.log
    """
    env_path = Path(".env")
    # Merge with actual environment, but prefer current process env
    values = {}
    if env_path.exists():
        try:
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    values[k.strip()] = v.strip().strip('"').strip("'")
        except Exception:
            pass
    # overlay os.environ
    for k in ("OPENAI_API_KEY", "DB_PATH", "DEPLOYMENTS_DIR"):
        if os.getenv(k):
            values[k] = os.getenv(k)

    openai_key = values.get("OPENAI_API_KEY")
    ok_key = bool(openai_key and len(openai_key) > 40)
    db_path = Path(values.get("DB_PATH") or "ai_factory/data/memory.db")
    dep_dir = Path(values.get("DEPLOYMENTS_DIR") or "deployments")

    # Ensure directories
    dep_dir.mkdir(parents=True, exist_ok=True)
    db_dir = db_path.parent
    db_dir.mkdir(parents=True, exist_ok=True)

    # Logging
    log_dir = Path("deployments")
    log_dir.mkdir(exist_ok=True)
    prefix = (openai_key[:7] + "...") if openai_key else "(none)"
    lines = [
        f"OPENAI_API_KEY: {'OK' if ok_key else 'MISSING/SHORT'} (prefix={prefix})",
        f"DB_PATH: {db_path} (dir exists={db_dir.exists()})",
        f"DEPLOYMENTS_DIR: {dep_dir} (exists={dep_dir.exists()})",
    ]
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(log_dir / "env_check.log", "a", encoding="utf-8") as f:
        f.write(f"{ts} | " + " | ".join(lines) + "\n")

