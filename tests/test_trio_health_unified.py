import os
from fastapi.testclient import TestClient

from ai_factory.main import app


def test_unified_trio_health_endpoints(monkeypatch):
    # Ensure unified host
    os.environ.setdefault('OLLAMA_HOST', 'http://127.0.0.1:11434')
    os.environ.setdefault('AI_FACTORY_LOCAL_STRATEGIST_MODEL', 'llama3.1:8b')
    os.environ.setdefault('AI_FACTORY_LOCAL_MEMORY_MODEL', 'qwen2.5:1.5b')
    os.environ.setdefault('AI_FACTORY_LOCAL_EXECUTION_MODEL', 'phi3:mini')

    # Patch only the httpx.Client used inside our modules to avoid breaking TestClient
    from ai_factory.advisor import advisor_service as svc
    from ai_factory.advisor import trio_manager as tm_mod

    class FakeResp:
        def __init__(self, model=None):
            self.status_code = 200
            self._model = model
            self.text = "ok"
        def json(self):
            return {"ok": True, "model": self._model}

    class FakeClient:
        def __init__(self, *a, **kw):
            pass
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False
        def get(self, url, *a, **kw):
            return FakeResp()
        def post(self, url, json=None, *a, **kw):
            return FakeResp(model=(json or {}).get('model'))

    monkeypatch.setattr(svc, 'httpx', type('X', (), {'Client': FakeClient}))
    monkeypatch.setattr(tm_mod, 'httpx', type('Y', (), {'Client': FakeClient}))

    client = TestClient(app)

    r = client.get('/advisor/trio_health')
    assert r.status_code == 200
    j = r.json()
    roles = j.get('roles', {})
    assert set(roles.keys()) == {'strategist','memory','executor'}
    assert all(v.get('healthy') for v in roles.values())

    r2 = client.get('/factory/info')
    assert r2.status_code == 200
    j2 = r2.json()
    health = j2.get('local_trio_health')
    assert isinstance(health, dict)
    # Depending on source (tm vs verify), structure may be dict of role->dict
    assert set(health.keys()) == {'strategist','memory','executor'}
