import os
from fastapi.testclient import TestClient
from ai_factory.main import app

client = TestClient(app)


def test_advisor_routes_local_when_healthy(monkeypatch):
    # Mock health endpoint via models call by monkeypatching httpx.Client.get
    import httpx
    real = httpx.Client.get
    def fake_get(self, url, *args, **kwargs):
        class R:
            status_code = 200
            def json(self):
                return {"models":["ok"]}
            text = "ok"
        if "/api/tags" in url:
            return R()
        return real(self, url, *args, **kwargs)
    monkeypatch.setattr(httpx.Client, 'get', fake_get)

    r = client.post('/advisor/route', json={"goal": "build fastapi app"})
    assert r.status_code == 200
    j = r.json()
    assert j['backend'] in ("local","openai")
    # With health OK and privacy strict=true default, should be local strategist
    assert j['role'] == 'strategist'


def test_advisor_fallback_to_openai_when_down(monkeypatch):
    import httpx
    def fail_get(self, url, *args, **kwargs):
        raise httpx.ConnectError("down")
    monkeypatch.setattr(httpx.Client, 'get', fail_get)
    r = client.post('/advisor/route', json={"goal": "build fastapi app"})
    assert r.status_code == 200
    j = r.json()
    assert j['backend'] == 'openai'

