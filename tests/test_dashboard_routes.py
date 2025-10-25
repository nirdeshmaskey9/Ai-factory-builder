import os
from fastapi.testclient import TestClient

os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app

client = TestClient(app)


def test_dashboard_index():
    res = client.get("/dashboard")
    assert res.status_code == 200
    assert "Factory Overview" in res.text


def test_dashboard_runs():
    # Ensure at least one run exists
    r = client.post(
        "/orchestrator/run",
        json={"goal": "dashboard-runs smoke", "max_attempts": 1, "deploy": False},
    )
    assert r.status_code == 200
    res = client.get("/dashboard/runs")
    assert res.status_code == 200
    assert "Recent Orchestrator Runs" in res.text


def test_dashboard_summary():
    r = client.post(
        "/orchestrator/run",
        json={"goal": "dashboard-summary smoke", "max_attempts": 1, "deploy": False},
    )
    assert r.status_code == 200
    run_id = r.json()["run_id"]
    res = client.get(f"/dashboard/summary/{run_id}")
    assert res.status_code == 200
    assert f"Run Summary #{run_id}" in res.text

