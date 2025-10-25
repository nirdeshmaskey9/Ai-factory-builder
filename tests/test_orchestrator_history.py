import os
from fastapi.testclient import TestClient

os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app

client = TestClient(app)


def test_orchestrator_history_endpoint():
    # Trigger a run to ensure history is populated
    r = client.post(
        "/orchestrator/run",
        json={"goal": "history endpoint smoke", "max_attempts": 1, "deploy": False},
    )
    assert r.status_code == 200

    h = client.get("/orchestrator/history", params={"limit": 5, "sort": "desc"})
    assert h.status_code == 200
    arr = h.json()
    assert isinstance(arr, list) and len(arr) >= 1
    item = arr[0]
    for key in ("run_id", "goal", "status", "score", "timestamp"):
        assert key in item
    # Optional artifacts
    assert "report_path" in item

