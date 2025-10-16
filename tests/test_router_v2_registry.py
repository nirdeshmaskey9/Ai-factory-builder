import os
from fastapi.testclient import TestClient

os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app

client = TestClient(app)


def test_model_registry_update_and_list():
    # List baseline
    r0 = client.get("/router/models")
    assert r0.status_code == 200
    base = r0.json()
    assert any(m["model_name"] == "claude3" for m in base)

    # Update weight
    u = client.post("/router/update", json={"model_name": "claude3", "weight": 1.3, "capabilities": ["coding", "reasoning", "general"]})
    assert u.status_code == 200

    r1 = client.get("/router/models")
    assert r1.status_code == 200
    after = {m["model_name"]: m for m in r1.json()}
    assert abs(after["claude3"]["weight"] - 1.3) < 1e-6

    # Route a few tasks to update logs and rolling stats
    for _ in range(3):
        client.post("/router/route", json={"task_type": "coding"})

    logs = client.get("/router/logs", params={"limit": 3})
    assert logs.status_code == 200
    assert len(logs.json()) >= 1

