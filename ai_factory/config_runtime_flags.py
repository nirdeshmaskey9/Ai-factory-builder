"""
Runtime flags and usage tracking for the UI control panel.
"""
from __future__ import annotations

import os
from typing import Final


os.makedirs("logs/ui", exist_ok=True)
LOG_PATH: Final[str] = "logs/ui/usage.log"

# Safe defaults: start in mock mode
mock_mode: bool = True
api_tokens: int = 0
api_usd: float = 0.0


def _ts() -> str:
    try:
        import time
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    except Exception:
        return ""


def set_mock_mode(state: bool) -> None:
    global mock_mode
    mock_mode = bool(state)
    try:
        with open(LOG_PATH, "a", encoding="utf8") as f:
            f.write(f"[{_ts()}] [Toggle] mock_mode={mock_mode}\n")
    except Exception:
        pass


def add_usage(tokens: int, usd: float) -> None:
    global api_tokens, api_usd
    try:
        t = int(tokens or 0)
    except Exception:
        t = 0
    try:
        c = float(usd or 0.0)
    except Exception:
        c = 0.0
    api_tokens += t
    api_usd += c
    try:
        with open(LOG_PATH, "a", encoding="utf8") as f:
            f.write(f"[{_ts()}] +{t} tokens ≈ ${c:.5f} (live)\n")
    except Exception:
        pass
