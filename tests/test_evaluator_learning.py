import os
from fastapi.testclient import TestClient

os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app

client = TestClient(app)


def test_learning_stats_and_trends_and_weight_changes():
    # Apply a couple of rewards
    client.post("/evaluator/reward", json={"model_name": "gpt4", "task_type": "planning", "score_delta": 0.1})
    client.post("/evaluator/reward", json={"model_name": "gpt4", "task_type": "planning", "score_delta": 0.2})
    client.post("/evaluator/reward", json={"model_name": "gemini", "task_type": "design", "score_delta": -0.05})

    # Stats
    s = client.get("/evaluator/reward/stats")
    assert s.status_code == 200
    avgs = {a["model_name"]: a["avg_reward"] for a in s.json()["averages"]}
    assert "gpt4" in avgs

    # Trends
    t = client.get("/evaluator/reward/trends", params={"limit": 5})
    assert t.status_code == 200
    assert "recent" in t.json()

    # Learn and confirm models endpoint responds
    l = client.post("/evaluator/learn")
    assert l.status_code == 200
    m = client.get("/router/models")
    assert m.status_code == 200

