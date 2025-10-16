import os
from fastapi.testclient import TestClient

os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app

client = TestClient(app)


def _ensure_evaluation():
    # Create a supervisor session and evaluate it
    sr = client.post("/supervisor/run", json={"goal": "builder should improve score by re-run"})
    assert sr.status_code == 200
    st = client.get("/supervisor/status", params={"limit": 1})
    sid = st.json()[0]["id"]
    er = client.post("/evaluator/evaluate", json={"session_id": sid})
    assert er.status_code == 200
    return er.json()


def test_builder_rebuild_improves_or_same():
    eval_payload = _ensure_evaluation()
    ev_id = eval_payload["evaluation_id"]
    old = eval_payload["score"]

    br = client.post("/builder/rebuild", json={"evaluation_id": ev_id})
    assert br.status_code == 200
    data = br.json()
    assert data["revision_id"] > 0
    assert data["evaluation_id"] == ev_id
    assert data["new_score"] >= data["old_score"]
    assert data["status"] in ("improved", "same", "worse")

