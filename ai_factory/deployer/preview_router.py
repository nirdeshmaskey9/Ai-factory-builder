from __future__ import annotations

from fastapi import APIRouter, HTTPException
import time
try:
    import psutil  # type: ignore
except Exception:
    psutil = None  # type: ignore

from ai_factory.deployer.preview_service import (
    run_preview,
    stop_preview,
    stop_all_previews,
    active_previews,
    guardian_running,
    start_guardian,
)


router = APIRouter(prefix="/deployer", tags=["deployer-preview"])


@router.get("/preview/stop/{build_id}")
def stop(build_id: str):
    return stop_preview(build_id)


@router.get("/preview/stop_all")
def stop_all():
    return stop_all_previews()


@router.get("/preview/{build_id}")
def preview(build_id: str):
    try:
        return run_preview(build_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def deployer_health():
    try:
        if not guardian_running:
            start_guardian()
        data = []
        for bid, info in active_previews.items():
            pid = info.get("pid")
            if psutil is not None:
                try:
                    if not psutil.pid_exists(pid):
                        continue
                except Exception:
                    pass
            started = info.get("start", time.time())
            data.append({
                "build_id": bid,
                "pid": pid,
                "port": info.get("port"),
                "uptime_s": round(time.time() - started, 1),
            })
        return {"active_previews": len(data), "previews": data, "guardian_running": guardian_running}
    except Exception as e:
        return {"error": str(e)}
