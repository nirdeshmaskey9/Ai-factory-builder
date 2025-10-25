import os
from fastapi.testclient import TestClient

os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app

client = TestClient(app)


def test_memory_ui_and_factory_info():
    # Seed one entry
    p = {"run_id": None, "goal": "CLI app", "summary": "ok", "tags": ["cli"], "score": None}
    r = client.post("/memory/store", json=p)
    assert r.status_code in (200, 201)
    mid = r.json()["id"]

    r1 = client.get("/dashboard/memory")
    assert r1.status_code == 200

    r2 = client.get(f"/dashboard/memory/{mid}")
    assert r2.status_code == 200

    info = client.get("/factory/info").json()
    assert info.get("memory_enabled") is True
    assert str(info.get("version")).startswith("v3.1")
