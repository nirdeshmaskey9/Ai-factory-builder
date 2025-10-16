import os
from fastapi.testclient import TestClient

os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app
from ai_factory.evaluator.evaluator_store import get_recent

client = TestClient(app)


def _latest_supervisor_id():
    r = client.get("/supervisor/status", params={"limit": 1})
    if r.status_code == 200 and r.json():
        return r.json()[0]["id"]
    rr = client.post("/supervisor/run", json={"goal": "evaluate a simple hello script"})
    assert rr.status_code == 200
    r2 = client.get("/supervisor/status", params={"limit": 1})
    return r2.json()[0]["id"]


def test_evaluator_run_and_persist():
    sid = _latest_supervisor_id()
    r = client.post("/evaluator/evaluate", json={"session_id": sid})
    assert r.status_code == 200
    data = r.json()
    assert 0.0 <= data["score"] <= 1.0
    assert data["status"] in ("pass", "improve", "fail")
    assert isinstance(data.get("feedback"), str) and len(data["feedback"]) > 0
    # DB persisted
    rows = get_recent(limit=5)
    assert any(row.session_id == sid for row in rows)

