from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Callable, Awaitable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ai_factory.memory.memory_store import log_event
from ai_factory.memory.memory_embeddings import add_to_memory

logger = logging.getLogger(__name__)


class MemoryLoggerMiddleware(BaseHTTPMiddleware):
    """
    Middleware that:
    - captures /planner/dispatch request + response
    - writes an event to SQLite
    - indexes response text into the Chroma vector store
    - adds X-Request-ID and X-Duration headers
    """

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if request.url.path.startswith("/planner/dispatch"):
            req_id = str(uuid.uuid4())
            started = time.time()

            # Read and preserve request body for downstream handler
            try:
                body_bytes = await request.body()
                # Starlette caches request._body so downstream can read again
                payload = json.loads(body_bytes.decode("utf-8") or "{}")
            except Exception:
                payload = {}

            response = await call_next(request)

            # Try to read response body safely
            content_bytes = b""
            try:
                # Most Response types (JSONResponse) have .body ready
                content_bytes = getattr(response, "body", b"") or b""
                if not content_bytes:
                    # Fallback: drain iterator and rebuild
                    async for chunk in response.body_iterator:  # type: ignore[attr-defined]
                        content_bytes += chunk
            except Exception:
                pass

            # Log to DB and index
            try:
                text_resp = content_bytes.decode("utf-8", errors="ignore")
                log_event(
                    request_id=req_id,
                    task_type=str(payload.get("task_type", "unknown")),
                    prompt=str(payload.get("prompt", "")),
                    response=text_resp,
                )
                # Index prompt + response for better recall
                to_index = f"task_type={payload.get('task_type','unknown')}\nPROMPT:\n{payload.get('prompt','')}\nRESPONSE:\n{text_resp}"
                add_to_memory(req_id, to_index)
            except Exception as e:
                logger.exception("Memory logging/indexing error: %s", e)

            # Add headers and return original response when possible
            duration = time.time() - started
            response.headers["X-Request-ID"] = req_id
            response.headers["X-Duration"] = str(round(duration, 3))

            if content_bytes and not getattr(response, "body", None):
                # If we drained a streaming response, rebuild it
                return Response(
                    content=content_bytes,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type,
                )
            return response

        # Non-planner routes pass through
        return await call_next(request)

class DebugLoggerMiddleware(BaseHTTPMiddleware):
    """
    Optional lightweight middleware to annotate /debugger/* requests with timing headers.
    Persistence and indexing happen in the route itself.
    """

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if request.url.path.startswith("/debugger/"):
            req_id = str(uuid.uuid4())
            started = time.time()
            response = await call_next(request)
            duration = time.time() - started
            response.headers["X-Debug-Request-ID"] = req_id
            response.headers["X-Debug-Duration"] = str(round(duration, 3))
            return response
        return await call_next(request)

class SupervisorLoggerMiddleware(BaseHTTPMiddleware):
    """
    Optional timing middleware for /supervisor/* routes. Safe no-op otherwise.
    """

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if request.url.path.startswith("/supervisor/"):
            req_id = str(uuid.uuid4())
            started = time.time()
            response = await call_next(request)
            duration = time.time() - started
            response.headers["X-Supervisor-Request-ID"] = req_id
            response.headers["X-Supervisor-Duration"] = str(round(duration, 3))
            return response
        return await call_next(request)

class EvaluatorLoggerMiddleware(BaseHTTPMiddleware):
    """
    Optional timing middleware for /evaluator/* routes. Safe no-op otherwise.
    """

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if request.url.path.startswith("/evaluator/"):
            req_id = str(uuid.uuid4())
            started = time.time()
            response = await call_next(request)
            duration = time.time() - started
            response.headers["X-Evaluator-Request-ID"] = req_id
            response.headers["X-Evaluator-Duration"] = str(round(duration, 3))
            return response
        return await call_next(request)
