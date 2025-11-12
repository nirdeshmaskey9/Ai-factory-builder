from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Path
from typing import Dict, Any
import asyncio
import json
import os

from ai_factory.orchestrator.orchestrator_store import list_runs


router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/runs")
async def ws_runs(ws: WebSocket):
    await ws.accept()
    try:
        # Initial snapshot
        rows = list_runs(limit=5, sort="desc")
        payload = [
            {
                "run_id": r.id,
                "goal": r.goal,
                "status": r.status,
                "score": r.evaluation_score,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            }
            for r in rows
        ]
        await ws.send_text(json.dumps({"type": "init", "runs": payload}))
        prev_len = len(rows)
        # Polling loop
        while True:
            await asyncio.sleep(2.0)
            rows = list_runs(limit=1, sort="desc")
            if len(rows) >= 1 and prev_len != len(rows):
                r = rows[0]
                await ws.send_text(json.dumps({
                    "type": "update",
                    "run": {
                        "run_id": r.id,
                        "goal": r.goal,
                        "status": r.status,
                        "score": r.evaluation_score,
                        "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                    }
                }))
                prev_len = len(rows)
    except WebSocketDisconnect:
        return
    except Exception:
        # Never crash the server due to WS
        try:
            await ws.close()
        except Exception:
            pass


@router.websocket("/logs/{run_id}")
async def ws_logs(ws: WebSocket, run_id: int = Path(..., ge=1)):
    await ws.accept()
    try:
        orch_path = os.path.join("logs", "orchestrator", f"run_{run_id}.json")
        sup_path = os.path.join("logs", "supervisor", f"report_{run_id}.json")
        def readf(p: str) -> Any:
            try:
                if not os.path.exists(p):
                    return None
                return json.load(open(p, "r", encoding="utf-8"))
            except Exception:
                return None
        # Initial
        await ws.send_text(json.dumps({
            "type": "init",
            "run": readf(orch_path),
            "supervisor": readf(sup_path),
        }))
        # Lightweight polling loop
        orch_m = os.path.getmtime(orch_path) if os.path.exists(orch_path) else 0
        sup_m = os.path.getmtime(sup_path) if os.path.exists(sup_path) else 0
        while True:
            await asyncio.sleep(2.0)
            changed = False
            if os.path.exists(orch_path):
                m = os.path.getmtime(orch_path)
                if m != orch_m:
                    orch_m = m
                    changed = True
            if os.path.exists(sup_path):
                m = os.path.getmtime(sup_path)
                if m != sup_m:
                    sup_m = m
                    changed = True
            if changed:
                await ws.send_text(json.dumps({
                    "type": "update",
                    "run": readf(orch_path),
                    "supervisor": readf(sup_path),
                }))
    except WebSocketDisconnect:
        return
    except Exception:
        try:
            await ws.close()
        except Exception:
            pass

