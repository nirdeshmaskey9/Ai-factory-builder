import os
from fastapi.testclient import TestClient

os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app

client = TestClient(app)


def test_runs_export_json_and_csv():
    client.post("/orchestrator/run", json={"goal": "export test", "max_attempts": 1})
    rj = client.get("/dashboard/runs", params={"download": "json"})
    assert rj.status_code == 200
    assert isinstance(rj.json(), list)
    rc = client.get("/dashboard/runs", params={"download": "csv"})
    assert rc.status_code == 200
    assert "run_id,goal,status,score,duration_sec,timestamp" in rc.text

