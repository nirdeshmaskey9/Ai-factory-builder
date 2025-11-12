from __future__ import annotations

import asyncio
import os
import signal
from typing import Optional

from ai_factory.deployer import deployer_store
from ai_factory.services import deployer_service as svc


_TASK: Optional[asyncio.Task] = None


async def _loop():
    from ai_factory.deployer.deployer_store import get_recent
    while True:
        try:
            rows = get_recent(limit=100)
            for d in rows:
                try:
                    if str(getattr(d, "status", "")).lower() == "running":
                        pid = deployer_store.get_pid(d.id)
                        alive = False
                        if pid:
                            try:
                                # os.kill(pid, 0) raises if not running on POSIX; on Windows it will error for invalid
                                os.kill(int(pid), 0)
                                alive = True
                            except Exception:
                                alive = False
                        if not alive:
                            # attempt restart using stored path and port
                            path = deployer_store.get_deploy_path(d.id)
                            if path and d.port:
                                proc = svc.launch_app(__import__('pathlib').Path(path), int(d.port))
                                deployer_store.update_status(d.id, "running", notes=f"watchdog restart pid={proc.pid}")
                                svc.register_process(d.id, proc)
                except Exception:
                    continue
        except Exception:
            pass
        await asyncio.sleep(60)


def start_watchdog() -> None:
    global _TASK
    try:
        loop = asyncio.get_running_loop()
        if _TASK is None or _TASK.done():
            _TASK = loop.create_task(_loop())
    except RuntimeError:
        # no running loop; skip
        pass

