import os
from fastapi.testclient import TestClient
import pytest

os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app

client = TestClient(app)


@pytest.mark.timeout(10)
def test_ws_runs_initial_message():
    # Ensure at least one run exists
    client.post("/orchestrator/run", json={"goal": "ws runs", "max_attempts": 1})
    with client.websocket_connect("/ws/runs") as ws:
        data = ws.receive_json()
        assert data.get("type") == "init"
        assert "runs" in data


@pytest.mark.timeout(10)
def test_ws_logs_initial_message():
    r = client.post("/orchestrator/run", json={"goal": "ws logs", "max_attempts": 1})
    run_id = r.json()["run_id"]
    with client.websocket_connect(f"/ws/logs/{run_id}") as ws:
        data = ws.receive_json()
        assert data.get("type") == "init"
        assert "run" in data
        assert "supervisor" in data

