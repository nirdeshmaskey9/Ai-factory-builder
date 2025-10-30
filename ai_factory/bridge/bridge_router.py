from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from pathlib import Path
import json
import time

from ai_factory.bridge.bridge_service import handle_chat, bridge_status


router = APIRouter(prefix="/bridge", tags=["bridge"])


class ChatRequest(BaseModel):
    user_input: str
    session_id: Optional[str] = None
    timestamp: Optional[str] = None


@router.post("/chat")
def chat(req: ChatRequest) -> Dict[str, Any]:
    try:
        result = handle_chat(req.user_input, session_id=req.session_id, timestamp=req.timestamp)
        # Log request/response minimal
        try:
            Path("logs").mkdir(exist_ok=True)
            with open("logs/bridge.log", "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "event": "chat",
                    "len": len(result.get("response_text") or ""),
                }) + "\n")
        except Exception:
            pass
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class SummarizeRequest(BaseModel):
    conversation_id: str


@router.post("/summarize")
def summarize(req: SummarizeRequest) -> Dict[str, Any]:
    from ai_factory.memory.memory_agent import generate_context_summary
    summ = generate_context_summary(req.conversation_id)
    return {"summary": summ}


@router.get("/status")
def status() -> Dict[str, Any]:
    return bridge_status()

