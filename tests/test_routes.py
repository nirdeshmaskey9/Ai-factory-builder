from fastapi.testclient import TestClient
from ai_factory.main import app


client = TestClient(app)


def test_factory_info():
    r = client.get("/factory/info")
    assert r.status_code == 200
    assert r.json().get("healthy") is True


def test_deployer_list():
    r = client.get("/deployer/list")
    assert r.status_code == 200


def test_factory_create_web():
    payload = {"goal": "Create a FastAPI app with /hello", "domain": "web"}
    r = client.post("/factory/create", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "build_id" in data and data.get("domain") == "web"

