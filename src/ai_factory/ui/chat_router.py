from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
from fastapi.templating import Jinja2Templates
from typing import Dict, Any
import asyncio
import json
import time

from ai_factory.bridge.bridge_service import process_bridge_chat


templates = Jinja2Templates(directory="src/ai_factory/ui/templates")
router = APIRouter(tags=["Chat UI"])


@router.get("/chat")
def chat_page(request: Request):
    return templates.TemplateResponse(request, "chat.html", {"title": "JoJo Planet - Chat"})


@router.websocket("/ws/chat")
async def chat_ws(ws: WebSocket):
    await ws.accept()
    try:
        session_id = "ui-session"
        # Greet
        await ws.send_text(json.dumps({
            "role": "assistant",
            "content": "Hello, I'm JoJo. How are you feeling today?",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }))
        while True:
            text = await ws.receive_text()
            try:
                payload: Dict[str, Any] = json.loads(text)
                user_input = str(payload.get("user_input") or payload.get("content") or text)
                if not user_input:
                    await asyncio.sleep(0)
                    continue
            except Exception:
                user_input = text
            # Echo user record
            await ws.send_text(json.dumps({
                "role": "user",
                "content": user_input,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }))
            # Process via hybrid bridge (local-first, safe fallback)
            result = process_bridge_chat(user_input=user_input, session_id=session_id)
            await ws.send_text(json.dumps({
                "role": "assistant",
                "content": result.get("response_text") or "",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }))
    except WebSocketDisconnect:
        return
    except Exception:
        try:
            await ws.close()
        except Exception:
            pass

