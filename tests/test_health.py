from fastapi.testclient import TestClient
from ai_factory.main import app

client = TestClient(app)


def test_healthcheck_ok():
    r = client.get("/healthcheck")
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "ok"
    assert data.get("phase") == 1
