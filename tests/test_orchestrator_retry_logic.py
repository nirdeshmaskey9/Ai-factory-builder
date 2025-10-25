import os
from fastapi.testclient import TestClient

os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app


client = TestClient(app)


def test_orchestrator_retry_logic(monkeypatch):
    # Force a low score then a high score across attempts
    state = {"count": 0}

    def fake_eval_session(session_id: int):
        state["count"] += 1
        if state["count"] == 1:
            return {"score": 0.4, "evaluation_id": 123}
        return {"score": 0.8, "evaluation_id": 124}

    # Ensure supervisor returns a stable structure
    def fake_run_supervisor(goal: str):
        return {"request_id": "x", "goal": goal, "plan": {"steps": []}, "context": [], "result": "ok", "status": "ok"}

    # Force repair decision on the first attempt
    def fake_should_repair(prev, new, attempt, max_attempts):
        return attempt == 1

    import ai_factory.orchestrator.orchestrator_agent as orch
    monkeypatch.setattr(orch, "eval_session", fake_eval_session)
    monkeypatch.setattr(orch, "run_supervisor", fake_run_supervisor)
    monkeypatch.setattr(orch, "should_repair", fake_should_repair)

    r = client.post(
        "/orchestrator/run",
        json={"goal": "retry test goal", "max_attempts": 2, "deploy": False},
    )
    assert r.status_code == 200
    data = r.json()
    # Should have taken 2 attempts due to the forced retry
    assert data["attempts"] >= 2
    assert data["status"] in ("success", "deployed", "partial", "failed")

