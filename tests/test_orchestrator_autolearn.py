import os
from fastapi.testclient import TestClient

os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"
os.environ["ADMIN_MODE"] = "true"

from ai_factory.main import app

client = TestClient(app)


def test_orchestrator_auto_learn_creates_memory_entry():
    r = client.post(
        "/orchestrator/run",
        json={"goal": "autolearn smoke", "max_attempts": 1, "deploy": False},
    )
    assert r.status_code == 200
    run_id = r.json()["run_id"]

    # Search for tag-based hit
    sr = client.get("/memory/search", params={"q": "orchestrator", "limit": 20})
    assert sr.status_code == 200
    results = sr.json().get("results", [])
    assert any((row.get("run_id") == run_id) or ("orchestrator" in (row.get("tags") or "")) for row in results)

