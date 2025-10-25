import os
from fastapi.testclient import TestClient

os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app


client = TestClient(app)


def test_orchestrator_run_success_and_report_file():
    r = client.post(
        "/orchestrator/run",
        json={"goal": "build a minimal hello-world app", "max_attempts": 1, "deploy": False},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["run_id"] > 0
    assert data["attempts"] >= 1
    assert data["status"] in ("success", "deployed", "partial", "failed")
    # Report file exists
    report_path = data.get("report_path")
    assert report_path
    assert os.path.exists(report_path)

