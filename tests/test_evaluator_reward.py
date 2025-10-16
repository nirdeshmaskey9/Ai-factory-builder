import os
from fastapi.testclient import TestClient

os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app

client = TestClient(app)


def test_reward_updates_router_weight_and_memory():
    # Baseline model list
    r0 = client.get("/router/models")
    assert r0.status_code == 200
    models = {m["model_name"]: m for m in r0.json()}
    base_w = models["claude3"]["weight"]

    # Positive delta -> increase weight
    r = client.post("/evaluator/reward", json={"model_name": "claude3", "task_type": "coding", "score_delta": 0.4, "notes": "good run"})
    assert r.status_code == 200
    data = r.json()
    assert data["reward"] > 0
    assert data["updated_weight"] > base_w

    # Memory contains EVAL v9 snippet (lexical)
    ms = client.get("/memory/search", params={"q": "EVAL v9", "n": 2})
    assert ms.status_code == 200
    assert "results" in ms.json()

