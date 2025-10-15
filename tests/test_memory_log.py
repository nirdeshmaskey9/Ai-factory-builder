import os
from fastapi.testclient import TestClient

# Force FAKE embeddings to avoid model downloads during tests
os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app
from ai_factory.memory.memory_store import find_by_request_id

client = TestClient(app)


def test_log_and_retrieve_via_middleware():
    payload = {"prompt": "Write a testable function; add unit tests", "task_type": "general"}
    r = client.post("/planner/dispatch", json=payload)
    assert r.status_code == 200
    req_id = r.headers.get("X-Request-ID")
    assert req_id is not None
    # Verify it was logged in SQLite
    rows = find_by_request_id(req_id)
    assert any(evt.request_id == req_id for evt in rows)
