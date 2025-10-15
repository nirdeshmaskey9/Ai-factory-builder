import os
from fastapi.testclient import TestClient

# Force FAKE embeddings to avoid model downloads during tests
os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app
from ai_factory.debugger.debugger_store import find_by_request_id

client = TestClient(app)


def test_debugger_run_success_and_log():
    payload = {"code": "print('hello-debug')", "language": "python"}
    r = client.post("/debugger/run", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["exit_code"] == 0
    assert "hello-debug" in data["stdout"]
    req_id = data["request_id"]
    rows = find_by_request_id(req_id)
    assert any(row.request_id == req_id for row in rows)

