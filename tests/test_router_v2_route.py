import os
from fastapi.testclient import TestClient

os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app

client = TestClient(app)


def test_route_planning_coding_design_and_logs():
    # planning -> expect gpt4 most often
    r1 = client.post("/router/route", json={"task_type": "planning"})
    assert r1.status_code == 200
    m1 = r1.json()["model_name"]
    # coding -> claude3 preferred
    r2 = client.post("/router/route", json={"task_type": "coding"})
    assert r2.status_code == 200
    m2 = r2.json()["model_name"]
    # design -> gemini preferred
    r3 = client.post("/router/route", json={"task_type": "design"})
    assert r3.status_code == 200
    m3 = r3.json()["model_name"]

    assert isinstance(r1.json().get("dispatch_id"), str)
    assert "duration_ms" in r1.json() and "score" in r1.json()

    # Sanity check model choices (not strict)
    assert m1 in ("gpt4", "claude3", "gemini")
    assert m2 in ("claude3", "gpt4", "gemini")
    assert m3 in ("gemini", "gpt4", "claude3")

    # Logs endpoint should have entries
    logs = client.get("/router/logs", params={"limit": 5})
    assert logs.status_code == 200
    assert isinstance(logs.json(), list) and len(logs.json()) >= 1

    # Memory should contain ROUTER v8 snippet (lexical check)
    ms = client.get("/memory/search", params={"q": "ROUTER v8", "n": 2})
    assert ms.status_code == 200
    assert "results" in ms.json()

