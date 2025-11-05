from __future__ import annotations

import types
import builtins

import ai_factory.advisor.local_trio as lt
from ai_factory.advisor.advisor_service import verify_local_health


class _Resp:
    def __init__(self, status_code: int, text: str = "ok") -> None:
        self.status_code = status_code
        self._text = text

    def json(self):
        return {"ok": True}

    @property
    def text(self):
        return self._text


class _Client:
    def __init__(self, timeout: float = 1.0):
        self.timeout = timeout

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, url: str):
        # Simulate /api/version OK
        return _Resp(200)

    def post(self, url: str, json: dict):
        # Simulate /api/generate OK
        return _Resp(200)


def test_trio_v4_definition():
    assert isinstance(lt.local_trio, dict)
    assert set(lt.local_trio.keys()) == {"strategist", "memory", "executor"}
    assert lt.local_trio["strategist"] == "phi3:medium"
    assert lt.local_trio["memory"] == "mistral"
    assert lt.local_trio["executor"] == "phi3:mini"


def test_verify_local_health_monkeypatch(monkeypatch):
    # Patch httpx.Client used by advisor_service
    import httpx

    monkeypatch.setattr(httpx, "Client", _Client)
    res = verify_local_health()
    roles = res.get("roles", {})
    assert set(roles.keys()) == {"strategist", "memory", "executor"}
    assert all(roles[r]["healthy"] for r in roles)

