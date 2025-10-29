import httpx
from fastapi.testclient import TestClient
from ai_factory.main import app

client = TestClient(app)


def test_parallel_serve_trio_health(monkeypatch):
    real_post = httpx.Client.post
    def ok_post(self, url, json=None, *a, **kw):
        if '/api/generate' in url:
            class R:
                status_code = 200
            return R()
        return real_post(self, url, json=json, *a, **kw)
    monkeypatch.setattr(httpx.Client, 'post', ok_post)

    r = client.get('/advisor/trio_health')
    assert r.status_code == 200
    j = r.json()
    roles = j.get('roles', {})
    assert roles.get('strategist', {}).get('healthy') is True
    assert roles.get('memory', {}).get('healthy') is True
    assert roles.get('executor', {}).get('healthy') is True

