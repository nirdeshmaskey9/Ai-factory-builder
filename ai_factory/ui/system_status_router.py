from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any

from ai_factory.advisor.advisor_service import verify_local_health

try:
    from ai_factory.version import __version__ as _VER, __milestone__ as _MS
except Exception:
    _VER, _MS = None, None


router = APIRouter(prefix="/ui", tags=["System Status"])


@router.get("/system_status")
def system_status(request: Request) -> JSONResponse:
    ver = _VER or "unknown"
    milestone = _MS or ""
    health = verify_local_health().get("roles", {})
    payload: Dict[str, Any] = {
        "version": ver,
        "milestone": milestone,
        "bridge_mode": "hybrid",
        "trio_health": health,
    }
    return JSONResponse(payload)

