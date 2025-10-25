import os
from fastapi.testclient import TestClient

os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app

client = TestClient(app)


def test_store_and_search_and_delete():
    payload = {
        "run_id": None,
        "goal": "Build a FastAPI service with memory",
        "summary": "Goal: Build service. Steps: plan, code, test. Status: ok.",
        "tags": ["fastapi", "web", "memory"],
        "score": 0.9,
    }
    r = client.post("/memory/store", json=payload)
    assert r.status_code in (200, 201)
    mid = r.json()["id"]
    # Search
    r2 = client.get("/memory/search", params={"q": "fastapi", "limit": 5})
    assert r2.status_code == 200
    hits = r2.json().get("results", [])
    assert any(h.get("id") == mid for h in hits)
    # Delete (soft)
    r3 = client.delete(f"/memory/{mid}")
    assert r3.status_code == 200
    r4 = client.get("/memory/search", params={"q": "fastapi", "limit": 50})
    hits2 = r4.json().get("results", [])
    assert not any(h.get("id") == mid for h in hits2)

