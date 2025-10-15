from fastapi.testclient import TestClient
from ai_factory.main import app

client = TestClient(app)


def test_dispatch_minimal():
    payload = {"prompt": "Set up a new repo; write README; add CI", "task_type": "general"}
    r = client.post("/planner/dispatch", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["task_type"] == "general"
    assert isinstance(data["steps"], list) and len(data["steps"]) >= 1
    assert "request_id" in data and len(data["request_id"]) > 0
    assert data["estimated_tokens"] >= 32


def test_dispatch_validation_error():
    payload = {"prompt": "   ", "task_type": "general"}
    r = client.post("/planner/dispatch", json=payload)
    # Pydantic raises validation at FastAPI layer -> 422
    assert r.status_code in (400, 422)


def test_dispatch_task_type_enum():
    payload = {"prompt": "Write tests", "task_type": "coding"}
    r = client.post("/planner/dispatch", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["task_type"] == "coding"
    # coding path should include scaffold step at index 0
    assert any("Scaffold repo" in s["action"] for s in data["steps"])
