import os
import time
from fastapi.testclient import TestClient

os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app

client = TestClient(app)


def _ensure_session():
    r = client.post("/supervisor/run", json={"goal": "deploy a tiny app"})
    assert r.status_code == 200
    st = client.get("/supervisor/status", params={"limit": 1})
    assert st.status_code == 200 and st.json()
    return st.json()[0]["id"]


def test_deployer_deploy_and_status():
    sid = _ensure_session()
    r = client.post("/deployer/deploy", json={"session_id": sid})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] in ("running", "stopped")
    dep_id = data["deployment_id"]

    # Check status endpoint
    time.sleep(0.2)
    s = client.get(f"/deployer/status/{dep_id}")
    assert s.status_code == 200
    sd = s.json()
    assert sd["deployment_id"] == dep_id
    assert "status" in sd

