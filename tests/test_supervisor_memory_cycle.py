import os
from fastapi.testclient import TestClient

os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app

client = TestClient(app)


def test_supervisor_cycle_and_smoke_routes():
    # Run supervisor
    r = client.post("/supervisor/run", json={"goal": "write python code then test it"})
    assert r.status_code == 200
    data = r.json()
    assert "request_id" in data

    # Status listing
    r2 = client.get("/supervisor/status", params={"limit": 5})
    assert r2.status_code == 200
    assert isinstance(r2.json(), list)

    # History listing
    r3 = client.get("/supervisor/history", params={"limit": 5})
    assert r3.status_code == 200
    assert isinstance(r3.json(), list)

    # Smoke prior phases
    rp = client.post("/planner/dispatch", json={"prompt": "hello", "task_type": "general"})
    assert rp.status_code == 200
    rm = client.get("/memory/search", params={"q": "hello", "n": 1})
    assert rm.status_code == 200
    rd = client.post("/debugger/run", json={"code": "print('ok')", "language": "python"})
    assert rd.status_code == 200

