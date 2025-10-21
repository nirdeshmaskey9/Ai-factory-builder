from __future__ import annotations

from sqlalchemy.exc import OperationalError
from sqlalchemy import text
from pathlib import Path
import time

from ai_factory.memory.memory_db import engine, init_db


def startup_probe() -> None:
    """Attempt a trivial insert/select/delete cycle to validate DB connectivity.

    Writes diagnostics to ./logs/memory.log. Retries on lock.
    """
    init_db()
    Path("logs").mkdir(exist_ok=True)
    log = Path("logs/memory.log")
    attempts = 0
    while attempts < 3:
        attempts += 1
        try:
            with engine.begin() as conn:
                conn.execute(text("CREATE TABLE IF NOT EXISTS _probe (id INTEGER PRIMARY KEY, v TEXT)"))
                conn.execute(text("INSERT INTO _probe(v) VALUES ('ok')"))
                rows = list(conn.execute(text("SELECT count(*) FROM _probe")))
                conn.execute(text("DELETE FROM _probe"))
            log.write_text((log.read_text(encoding="utf-8") if log.exists() else "") + f"probe ok rows={rows[0][0]}\n", encoding="utf-8")
            return
        except OperationalError:
            time.sleep(0.05 * attempts)
        except Exception as e:
            # Log and exit silently
            log.write_text((log.read_text(encoding="utf-8") if log.exists() else "") + f"probe error: {e}\n", encoding="utf-8")
            return

