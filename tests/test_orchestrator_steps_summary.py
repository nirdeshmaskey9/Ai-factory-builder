import os
from fastapi.testclient import TestClient

os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app

client = TestClient(app)


def test_orchestrator_steps_and_summary_endpoints():
    r = client.post(
        "/orchestrator/run",
        json={"goal": "steps+summary check", "max_attempts": 1, "deploy": False},
    )
    assert r.status_code == 200
    data = r.json()
    run_id = data["run_id"]

    s = client.get(f"/orchestrator/steps/{run_id}")
    assert s.status_code == 200
    steps = s.json()
    assert isinstance(steps, list)
    if steps:  # may be empty in some flows
        assert "step_name" in steps[0]
        assert "step_status" in steps[0]

    sm = client.get(f"/orchestrator/summary/{run_id}")
    assert sm.status_code == 200
    summary = sm.json()
    assert "run" in summary and "steps" in summary and "supervisor" in summary
    # supervisor may be not_found if missing, but the key must exist
    assert isinstance(summary["steps"], list)

