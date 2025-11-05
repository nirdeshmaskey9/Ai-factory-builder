from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any
from pydantic import BaseModel

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
        "rag_enabled": r.rag_enabled,
        "tokens": r.api_tokens,
        "usd": r.api_usd,
    }
    return JSONResponse(payload)


@router.get("/control_state")
def get_control_state() -> JSONResponse:
    # Load persona from file if present
    persona = "builder"
    try:
        import json, os
        from pathlib import Path
        p = Path("logs/ui/control_state.json")
        if p.exists():
            persona = (json.loads(p.read_text(encoding="utf-8")).get("persona_mode") or "builder").lower()
    except Exception:
        pass
    return JSONResponse({
        "mock_mode": r.mock_mode,
        "rag_enabled": r.rag_enabled,
        "tokens": r.api_tokens,
        "usd": r.api_usd,
        "persona_mode": persona,
    })


class ControlStateIn(BaseModel):
    persona_mode: str | None = None


@router.post("/control_state")
def set_control_state(payload: ControlStateIn) -> JSONResponse:
    # Persist persona_mode only (other fields remain via runtime flags)
    import json
    from pathlib import Path
    persona = (payload.persona_mode or "builder").lower()
    Path("logs/ui").mkdir(parents=True, exist_ok=True)
    Path("logs/ui/control_state.json").write_text(json.dumps({"persona_mode": persona}), encoding="utf-8")
    return JSONResponse({"persona_mode": persona})


@router.post("/toggle_mock")
def toggle_mock() -> JSONResponse:
    r.set_mock_mode(not r.mock_mode)
    return JSONResponse({"mock_mode": r.mock_mode})


@router.post("/toggle_rag")
def toggle_rag() -> JSONResponse:
    r.set_rag_enabled(not r.rag_enabled)
    return JSONResponse({"rag_enabled": r.rag_enabled})
