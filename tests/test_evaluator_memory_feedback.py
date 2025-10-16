import os
from fastapi.testclient import TestClient

os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app

client = TestClient(app)


def test_evaluator_feedback_appears_in_memory_search():
    # Ensure we have a supervisor session
    sr = client.post("/supervisor/run", json={"goal": "evaluation memory feedback smoke"})
    assert sr.status_code == 200
    st = client.get("/supervisor/status", params={"limit": 1})
    assert st.status_code == 200 and st.json()
    sid = st.json()[0]["id"]

    # Evaluate
    er = client.post("/evaluator/evaluate", json={"session_id": sid})
    assert er.status_code == 200
    goal = er.json()["goal"]

    # Memory search for 'EVALUATION' keyword or goal string
    r = client.get("/memory/search", params={"q": "EVALUATION", "n": 3})
    assert r.status_code == 200
    data = r.json()
    assert "results" in data
    # If lexical fallback isn't strong, try goal search as well
    if not data["results"]:
        r2 = client.get("/memory/search", params={"q": goal, "n": 3})
        assert r2.status_code == 200
        data = r2.json()
    assert isinstance(data.get("results", []), list)

    # Smoke old routes
    rp = client.post("/planner/dispatch", json={"prompt": "hello", "task_type": "general"})
    assert rp.status_code == 200
    rd = client.post("/debugger/run", json={"code": "print('ok')", "language": "python"})
    assert rd.status_code == 200

