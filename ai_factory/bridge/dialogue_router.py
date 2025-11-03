from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any
import os
import json

from ai_factory.memory.dialogue_store import load_recent, save_session_summary
from ai_factory.bridge.chatgpt_proxy import call_chatgpt


router = APIRouter(prefix="/dialogue", tags=["Dialogue"])


@router.get("/recent")
def dialogue_recent(request: Request):
    sid = request.query_params.get("session") or request.cookies.get("jp_session") or "default"
    try:
        n = int(request.query_params.get("n") or 40)
    except Exception:
        n = 40
    turns = load_recent(sid, n=n)
    return JSONResponse(turns)


def _mock_summary(last_turns: list[dict[str, Any]]) -> Dict[str, Any]:
    # Deterministic mock
    topics = []
    for t in last_turns[-5:]:
        c = (t.get("content") or "").strip()
        if c:
            topics.append(c.split(". ")[0][:60])
    topic = topics[-1] if topics else "General conversation"
    return {
        "topic": topic,
        "key_facts": topics[:3],
        "tone": "upbeat",
        "decisions": [],
        "todos": [],
    }


@router.post("/close")
def dialogue_close(request: Request):
    sid = request.query_params.get("session") or request.cookies.get("jp_session") or "default"
    dry_run = (request.query_params.get("dry-run") or request.query_params.get("dry_run")) in ("1", "true", "True")
    last = load_recent(sid, n=50)
    # Build a compact prompt
    content = "\n".join([f"{t['role']}: {t['content']}" for t in last[-50:]])
    payload = {
        "sanitized_text": f"Summarize the following session into a concise JSON.\n\n{content}",
        "user_text": content,
        "context_additions": "",
        "memory_summary": "",
        "target_model": os.getenv("AI_FACTORY_CLOUD_MODEL", "gpt-4o"),
    }
    summary: Dict[str, Any]
    try:
        if os.getenv("OPENAI_API_KEY"):
            resp = call_chatgpt(payload)
            # Expect JSON in response_text; fallback to mock if parse fails
            txt = str(resp.get("response_text") or "{}")
            try:
                summary = json.loads(txt)
            except Exception:
                summary = _mock_summary(last)
        else:
            summary = _mock_summary(last)
    except Exception:
        summary = _mock_summary(last)
    if not dry_run:
        try:
            save_session_summary(sid, summary)
        except Exception:
            pass
    return JSONResponse(summary)


@router.post("/reinject")
def dialogue_reinject(request: Request):
    try:
        body = json.loads((request._body if hasattr(request, "_body") else None) or "{}")
    except Exception:
        body = {}
    # In the absence of real summary lookup by id, condense provided summary into a context string
    summary = body.get("summary") or {}
    if not summary and body.get("summary_id"):
        # In a minimal implementation, we can't lookup by id without extra query; return placeholder
        ctx = "Context ready from summary #{}".format(body.get("summary_id"))
    else:
        ctx = (summary.get("topic") or "")
    return JSONResponse({"context": ctx})

