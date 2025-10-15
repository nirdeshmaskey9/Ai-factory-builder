import os
from fastapi.testclient import TestClient

# Force FAKE embeddings to avoid model downloads during tests
os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app

client = TestClient(app)


def test_memory_search_endpoint_smoke():
    # Seed memory by triggering a planner call (middleware logs it and indexes)
    payload = {"prompt": "How to scaffold a repo and add CI", "task_type": "coding"}
    r1 = client.post("/planner/dispatch", json=payload)
    assert r1.status_code == 200

    # Now query the semantic search
    r2 = client.get("/memory/search", params={"q": "scaffold repository and continuous integration", "n": 2})
    assert r2.status_code == 200
    data = r2.json()
    assert "results" in data
    assert isinstance(data["results"], list)
