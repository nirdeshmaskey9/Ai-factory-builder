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

    # Support unified health check (GET /api/version + POST /api/generate)
    real_get = httpx.Client.get
    def ok_get(self, url, *args, **kwargs):
        if isinstance(url, str) and ("127.0.0.1:11434" in url or "/api/version" in url or "/api/tags" in url):
            class Resp:
                status_code = 200
                def json(self):
                    return {"version": "1.0.0"}
            return Resp()
        return real_get(self, url, *args, **kwargs)

    monkeypatch.setattr(httpx.Client, 'get', ok_get)

    # Ensure endpoint uses unified verify_local_health path (no trio_manager)
    try:
        from ai_factory.main import app as _app
        _app.state.trio_manager = None
    except Exception:
        pass

    r = client.get('/advisor/trio_health')
    assert r.status_code == 200
    j = r.json()
    # Support both shapes: {"roles": {...}} and legacy {...}
    if 'roles' not in j:
        j = {'roles': j}
    roles = j.get('roles', {})
    assert roles.get('strategist', {}).get('healthy') is True
    assert roles.get('memory', {}).get('healthy') is True
    assert roles.get('executor', {}).get('healthy') is True
