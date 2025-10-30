from __future__ import annotations

import os
import threading
from typing import Dict, Optional
import httpx
import logging
from logging.handlers import RotatingFileHandler


def _int(v: Optional[str], default: int) -> int:
    try:
        return int(v) if v is not None else default
    except Exception:
        return default


class LocalTrioManager:
    """Lightweight health monitor for a unified local Ollama daemon.

    Roles: strategist, memory, executor. All roles share one daemon
    at OLLAMA_HOST (default http://127.0.0.1:11434) and are addressed
    by model name rather than port.
    """

    def __init__(self) -> None:
        self.models = {
            "strategist": os.getenv("STRATEGIST_MODEL") or os.getenv("AI_FACTORY_LOCAL_STRATEGIST_MODEL", "llama3.1:8b"),
            "memory": os.getenv("MEMORY_MODEL") or os.getenv("AI_FACTORY_LOCAL_MEMORY_MODEL", "phi3:mini"),
            "executor": os.getenv("EXECUTOR_MODEL") or os.getenv("AI_FACTORY_LOCAL_EXECUTION_MODEL", "qwen2.5:1.5b"),
        }
        self.host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
        self.interval = float(os.getenv("AI_FACTORY_TRIO_INTERVAL", "60"))
        self.health_map: Dict[str, Dict[str, object]] = {
            r: {"healthy": False, "model": self.models[r], "restarts": 0}
            for r in self.models.keys()
        }
        self._thread: Optional[threading.Thread] = None
        self._stop_evt = threading.Event()

        # Logger
        self.log = logging.getLogger("ai_factory.trio_manager")
        self.log.setLevel(logging.INFO)
        try:
            os.makedirs("logs", exist_ok=True)
            fh = RotatingFileHandler("logs/trio_manager.log", maxBytes=512_000, backupCount=2, encoding="utf-8")
            fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
            self.log.addHandler(fh)
        except Exception:
            pass

    def _probe(self, role: str) -> bool:
        """Probe the shared Ollama daemon by generating a tiny response.

        Retries up to 3 times with exponential backoff (10s, 20s, 30s).
        """
        model = self.models.get(role) or ""
        delays = [10, 20, 30]
        # Allow shortening in tests
        try:
            base = int(os.getenv("AI_FACTORY_HEALTH_BACKOFF_BASE", "10"))
            delays = [base, base * 2, base * 3]
        except Exception:
            pass
        for attempt, delay in enumerate(delays, start=1):
            try:
                with httpx.Client(timeout=float(os.getenv("AI_FACTORY_LOCAL_TIMEOUT", "5"))) as c:
                    # Optional sanity check; do not fail if unavailable to allow tests with mocked POST
                    if attempt == 1:
                        try:
                            v = c.get(f"{self.host}/api/version")
                            if v.status_code != 200:
                                pass
                        except Exception:
                            pass
                    r = c.post(f"{self.host}/api/generate", json={"model": model, "prompt": "ping", "stream": False})
                    if r.status_code == 200:
                        # Attempt to confirm non-empty payload
                        try:
                            j = r.json()
                            txt_ok = bool(j)
                        except Exception:
                            txt_ok = bool(getattr(r, "text", ""))
                        if txt_ok:
                            return True
            except Exception:
                pass
            # Backoff before next attempt unless stopping
            if self._stop_evt.wait(timeout=delay):
                break
        return False

    def _loop(self) -> None:
        while not self._stop_evt.is_set():
            for role in ("strategist", "memory", "executor"):
                ok = self._probe(role)
                prev = bool(self.health_map[role]["healthy"])
                self.health_map[role]["healthy"] = ok
                if ok and not prev:
                    self.log.info("[TrioManager] %s healthy ✅", role.capitalize())
                if not ok:
                    # Soft restart only: log warning, no process management in single-daemon mode
                    self.log.warning("[TrioManager] %s unhealthy ❌", role.capitalize())
            # Sleep interval (overridable for tests)
            try:
                to = float(os.getenv("AI_FACTORY_TRIO_INTERVAL", str(self.interval)))
            except Exception:
                to = self.interval
            if self._stop_evt.wait(timeout=max(0.1, to)):
                break

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_evt.clear()
        self._thread = threading.Thread(target=self._loop, name="LocalTrioManager", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_evt.set()
        try:
            if self._thread:
                self._thread.join(timeout=2.0)
        except Exception:
            pass
        # No process management — single daemon only
