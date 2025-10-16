import os
from fastapi.testclient import TestClient

os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app

client = TestClient(app)


def test_deployer_list_and_rollback():
    # Ensure at least one deployment
    sr = client.post("/supervisor/run", json={"goal": "registry test"})
    assert sr.status_code == 200
    st = client.get("/supervisor/status", params={"limit": 1})
    sid = st.json()[0]["id"]
    dr = client.post("/deployer/deploy", json={"session_id": sid})
    assert dr.status_code == 200
    dep_id = dr.json()["deployment_id"]

    # List
    lst = client.get("/deployer/list", params={"limit": 5})
    assert lst.status_code == 200
    assert isinstance(lst.json(), list)

    # Rollback
    rb = client.post("/deployer/rollback", json={"deployment_id": dep_id})
    assert rb.status_code == 200
    assert rb.json()["status"] == "stopped"

