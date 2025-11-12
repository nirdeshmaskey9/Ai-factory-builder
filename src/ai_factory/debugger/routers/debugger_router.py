from __future__ import annotations

import json
import logging
import uuid
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Query

from ai_factory.debugger.debugger_runner import run_code
from ai_factory.debugger.debugger_store import log_run, get_recent, search_runs
from ai_factory.memory.memory_embeddings import add_to_memory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/debugger", tags=["debugger"])


@router.post("/run")
def run(payload: Dict[str, Any]):
    code = (payload or {}).get("code", "")
    language = (payload or {}).get("language", "python")
    if not code:
        raise HTTPException(status_code=400, detail="code must not be empty")

    req_id = str(uuid.uuid4())
    result = run_code(language=language, code=code, timeout=5)
    try:
        log_run(
            request_id=req_id,
            language=language,
            code=code,
            stdout=result.get("stdout", ""),
            stderr=result.get("stderr", ""),
            status=result.get("status", "error"),
        )

        # Index for semantic recall
        to_index = (
            f"DEBUGGER RUN\nlang={language}\nCODE:\n{code}\nSTDOUT:\n{result.get('stdout','')}\nSTDERR:\n{result.get('stderr','')}\nSTATUS:{result.get('status')}"
        )
        add_to_memory(req_id, to_index)
    except Exception:
        logger.exception("Failed to persist/index debugger run")

    return {
        "request_id": req_id,
        "stdout": result.get("stdout", ""),
        "stderr": result.get("stderr", ""),
        "exit_code": result.get("exit_code", -1),
        "status": result.get("status", "error"),
    }


@router.get("/logs")
def logs(limit: int = Query(10, ge=1, le=200)):
    rows = get_recent(limit=limit)
    return [
        {
            "id": r.id,
            "request_id": r.request_id,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            "language": r.language,
            "status": r.status,
        }
        for r in rows
    ]


@router.get("/search")
def search(q: str = Query(..., min_length=1), n: int = Query(5, ge=1, le=50)):
    matches = search_runs(q, limit=n)
    return {
        "query": q,
        "results": [
            {
                "id": r.id,
                "request_id": r.request_id,
                "language": r.language,
                "status": r.status,
                "snippet": (r.stdout or r.stderr or r.code)[:240],
            }
            for r in matches
        ],
    }

