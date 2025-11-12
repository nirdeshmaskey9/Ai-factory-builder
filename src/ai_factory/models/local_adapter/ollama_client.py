from __future__ import annotations

from typing import Tuple
import time
import httpx

from . import LocalBackendError


def generate(url: str, model: str, prompt: str, timeout: float = 60.0, mode: str = "completion") -> Tuple[str, int, int, int]:
    t0 = time.perf_counter()
    try:
        payload = {"model": model, "prompt": prompt, "stream": False}
        with httpx.Client(timeout=timeout) as c:
            r = c.post(url.rstrip("/") + "/api/generate", json=payload)
            if r.status_code >= 400:
                raise LocalBackendError(f"HTTP {r.status_code}: {r.text[:200]}")
            data = r.json()
    except Exception as e:
        raise LocalBackendError(str(e))
    latency_ms = int((time.perf_counter() - t0) * 1000)
    text = data.get("response") or data.get("text") or ""
    # Ollama doesn't always return token counts; use 0 if missing
    tokens_in = int(data.get("prompt_eval_count") or 0)
    tokens_out = int(data.get("eval_count") or 0)
    return text, latency_ms, tokens_in, tokens_out

