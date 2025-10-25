import os
from fastapi.testclient import TestClient

os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app

client = TestClient(app)


def test_rerun_endpoint():
    # Ensure there is at least one run
    r = client.post("/orchestrator/run", json={"goal": "rerun smoke", "max_attempts": 1})
    assert r.status_code == 200
    run_id = r.json()["run_id"]
    res = client.post(f"/rerun/{run_id}")
    assert res.status_code == 200
    j = res.json()
    assert "status" in j

