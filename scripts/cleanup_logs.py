from __future__ import annotations

import time
from pathlib import Path


def archive_logs(days: int = 7) -> int:
    logs = Path("logs")
    if not logs.exists():
        return 0
    archive = logs / "ARCHIVE"
    archive.mkdir(parents=True, exist_ok=True)
    now = time.time()
    threshold = days * 86400
    moved = 0
    for p in logs.iterdir():
        if p.name == "ARCHIVE":
            continue
        try:
            age = now - p.stat().st_mtime
        except Exception:
            continue
        if age > threshold:
            try:
                p.rename(archive / p.name)
                moved += 1
            except Exception:
                pass
    return moved


def main() -> int:
    moved = archive_logs(7)
    print(f"Archived {moved} old log file(s) to logs/ARCHIVE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

