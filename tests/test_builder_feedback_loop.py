import os
from fastapi.testclient import TestClient

os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app

client = TestClient(app)


def test_builder_feedback_in_memory_and_smoke():
    # Ensure there's a supervisor + evaluation
    sr = client.post("/supervisor/run", json={"goal": "builder feedback memory check"})
    assert sr.status_code == 200
    st = client.get("/supervisor/status", params={"limit": 1})
    sid = st.json()[0]["id"]
    er = client.post("/evaluator/evaluate", json={"session_id": sid})
    assert er.status_code == 200
    ev_id = er.json()["evaluation_id"]

    # Rebuild
    br = client.post("/builder/rebuild", json={"evaluation_id": ev_id})
    assert br.status_code == 200

    # Memory should contain rebuild snippet
    r = client.get("/memory/search", params={"q": "REBUILD v6", "n": 3})
    assert r.status_code == 200
    assert "results" in r.json()

    # Smoke existing routes
    rp = client.post("/planner/dispatch", json={"prompt": "hello", "task_type": "general"})
    assert rp.status_code == 200
    rsv = client.post("/supervisor/run", json={"goal": "another goal"})
    assert rsv.status_code == 200
    rev = client.post("/evaluator/evaluate", json={"goal": "another goal"})
    assert rev.status_code == 200

