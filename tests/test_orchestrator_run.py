import os
from fastapi.testclient import TestClient

os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app

client = TestClient(app)


def test_orchestrator_run_creates_record():
    r = client.post(
        "/orchestrator/run",
        json={"goal": "build a tiny notes API with one POST/GET endpoint", "max_attempts": 2, "deploy": False},
    )
    assert r.status_code == 200
    data = r.json()
    assert "run_id" in data and data["run_id"] > 0
    assert data["attempts"] >= 1
    assert data["status"] in ("success", "deployed", "partial", "failed")
    assert "request_id" in data

    s = client.get(f"/orchestrator/status/{data['run_id']}")
    assert s.status_code == 200
    payload = s.json()
    assert payload.get("run_id") == data["run_id"]

