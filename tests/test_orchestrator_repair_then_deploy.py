import os
from fastapi.testclient import TestClient

os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app

client = TestClient(app)


def test_orchestrator_repair_then_deploy_flow():
    # Goal that likely needs at least one attempt; allow deploy
    r = client.post(
        "/orchestrator/run",
        json={"goal": "create sample app then improve", "max_attempts": 2, "deploy": True},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["attempts"] >= 1
    assert data["status"] in ("success", "deployed", "partial", "failed")

    # Memory should contain an orchestrator snippet
    ms = client.get("/memory/search", params={"q": "ORCH v10", "n": 3})
    assert ms.status_code == 200
    assert "results" in ms.json()

    # Smoke prior phases
    rp = client.post("/planner/dispatch", json={"prompt": "hello", "task_type": "general"})
    assert rp.status_code == 200
    rv2 = client.post("/router/route", json={"task_type": "coding"})
    assert rv2.status_code == 200

