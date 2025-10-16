import os
from fastapi.testclient import TestClient

# Force FAKE embeddings to avoid model downloads during tests
os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app
from ai_factory.supervisor.supervisor_store import get_recent

client = TestClient(app)


def test_supervisor_run_persists_session():
    payload = {"goal": "create a tiny script and print hello"}
    r = client.post("/supervisor/run", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "request_id" in data and data["request_id"]
    assert data["goal"] == payload["goal"]
    assert isinstance(data.get("plan"), dict)
    assert isinstance(data.get("context"), list)
    assert isinstance(data.get("result"), str)
    assert data.get("status") in ("success", "partial", "error")

    rows = get_recent(limit=5)
    assert any(row.request_id == data["request_id"] for row in rows)

