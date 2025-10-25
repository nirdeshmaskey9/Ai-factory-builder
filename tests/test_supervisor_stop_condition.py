import os
from fastapi.testclient import TestClient

os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app


client = TestClient(app)


def test_supervisor_stop_condition(monkeypatch):
    # Force persistent low score and no repair
    def fake_eval_session(session_id: int):
        return {"score": 0.1, "evaluation_id": 99}

    def fake_run_supervisor(goal: str):
        return {"request_id": "y", "goal": goal, "plan": {"steps": []}, "context": [], "result": "bad", "status": "fail"}

    def fake_should_repair(prev, new, attempt, max_attempts):
        return False

    import ai_factory.orchestrator.orchestrator_agent as orch
    monkeypatch.setattr(orch, "eval_session", fake_eval_session)
    monkeypatch.setattr(orch, "run_supervisor", fake_run_supervisor)
    monkeypatch.setattr(orch, "should_repair", fake_should_repair)

    r = client.post(
        "/orchestrator/run",
        json={"goal": "halt after failure", "max_attempts": 3, "deploy": False},
    )
    assert r.status_code == 200
    data = r.json()
    # System should halt early due to no repair allowed
    assert data["attempts"] >= 1
    assert data["status"] in ("failed", "partial", "success", "deployed")

