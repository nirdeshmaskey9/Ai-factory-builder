import os
from fastapi.testclient import TestClient

os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app

client = TestClient(app)


def test_recall_for_run_overlap():
    # Seed two entries with overlapping tags and distinct run_ids
    p1 = {"run_id": 10101, "goal": "Web app with FastAPI", "summary": "web api ok", "tags": ["fastapi", "web"], "score": 0.5}
    p2 = {"run_id": 20202, "goal": "FastAPI dashboard", "summary": "dashboard ok", "tags": ["fastapi", "dashboard"], "score": 0.7}
    a = client.post("/memory/store", json=p1)
    b = client.post("/memory/store", json=p2)
    assert a.status_code in (200, 201) and b.status_code in (200, 201)
    # Recall for first run should include the second due to shared 'fastapi'
    r = client.get(f"/memory/recall/{p1['run_id']}")
    assert r.status_code == 200
    arr = r.json()
    assert any(x.get("run_id") == p2["run_id"] for x in arr)

