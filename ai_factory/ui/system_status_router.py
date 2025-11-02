from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any

from ai_factory.advisor.advisor_service import verify_local_health
from ai_factory import config_runtime_flags as r

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
        "mock_mode": r.mock_mode,
        "tokens": r.api_tokens,
        "usd": r.api_usd,
    }
    return JSONResponse(payload)


@router.get("/control_state")
def get_control_state() -> JSONResponse:
    return JSONResponse({
        "mock_mode": r.mock_mode,
        "tokens": r.api_tokens,
        "usd": r.api_usd,
    })


@router.post("/toggle_mock")
def toggle_mock() -> JSONResponse:
    r.set_mock_mode(not r.mock_mode)
    return JSONResponse({"mock_mode": r.mock_mode})
