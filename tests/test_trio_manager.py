import os
import time
import httpx
from fastapi.testclient import TestClient

os.environ.setdefault('AI_FACTORY_TRIO_INTERVAL', '0.2')

from ai_factory.main import app


def test_trio_manager_endpoint_parallel_mode(monkeypatch):
    # Strategist unhealthy once then healthy; others healthy via /api/generate
    state = {'count': 0}
    real_post = httpx.Client.post
    def fake_post(self, url, json=None, *a, **kw):
        if '/api/generate' in url:
            model = (json or {}).get('model', '')
            if 'llama' in model:
                state['count'] += 1
                class R:
                    status_code = 500 if state['count'] == 1 else 200
                return R()
            class R:
                status_code = 200
            return R()
        return real_post(self, url, json=json, *a, **kw)
    monkeypatch.setattr(httpx.Client, 'post', fake_post)

    client = TestClient(app)
    time.sleep(0.7)
    r = client.get('/advisor/trio_health')
    assert r.status_code == 200
    j = r.json()
    assert set(j.get('roles', {}).keys()) == {'strategist','memory','executor'}
