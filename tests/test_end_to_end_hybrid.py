import httpx
from fastapi.testclient import TestClient
from ai_factory.main import app

client = TestClient(app)


def test_end_to_end_hybrid_with_local_advisor(monkeypatch):
    # Make local healthy
    real_get = httpx.Client.get
    def fake_get(self, url, *args, **kwargs):
        if '/api/tags' in url:
            class R:
                status_code = 200
                def json(self):
                    return {"models":["ok"]}
                text = "ok"
            return R()
        return real_get(self, url, *args, **kwargs)
    monkeypatch.setattr(httpx.Client, 'get', fake_get)

    r = client.post('/orchestrator/run', json={"goal": "hello world web", "max_attempts": 1, "deploy": False})
    assert r.status_code == 200
    run_id = r.json()["run_id"]
    s = client.get(f'/dashboard/summary/{run_id}')
    assert s.status_code == 200
    assert 'Advisor Decision' in s.text
