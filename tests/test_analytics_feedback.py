import os
from fastapi.testclient import TestClient
import pytest

os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app

client = TestClient(app)


def test_analytics_stats_and_trends():
    # create a run to ensure data
    r = client.post("/orchestrator/run", json={"goal": "analytics smoke", "max_attempts": 1})
    assert r.status_code == 200
    s = client.get("/analytics/stats")
    assert s.status_code == 200
    data = s.json()
    for k in ("total_runs", "success_rate", "avg_duration", "log_dir_size_mb", "builds_count"):
        assert k in data
    t = client.get("/analytics/trends", params={"limit": 5})
    assert t.status_code == 200
    arr = t.json()
    assert isinstance(arr, list) and len(arr) <= 5


def test_feedback_roundtrip():
    r = client.post("/orchestrator/run", json={"goal": "feedback smoke", "max_attempts": 1})
    run_id = r.json()["run_id"]
    post = client.post("/feedback", json={"run_id": run_id, "rating": "up", "comment": "looks good"})
    assert post.status_code == 200
    get = client.get(f"/feedback/{run_id}")
    assert get.status_code == 200
    items = get.json()
    assert any(i.get("comment") == "looks good" for i in items)

