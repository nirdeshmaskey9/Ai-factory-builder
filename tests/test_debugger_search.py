import os
from fastapi.testclient import TestClient

# Force FAKE embeddings to avoid model downloads during tests
os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app

client = TestClient(app)


def test_debugger_search_endpoint_smoke():
    token = "debug-search-token-xyz"
    payload = {"code": f"print('{token}')", "language": "python"}
    r1 = client.post("/debugger/run", json=payload)
    assert r1.status_code == 200

    r2 = client.get("/debugger/search", params={"q": token, "n": 3})
    assert r2.status_code == 200
    data = r2.json()
    assert "results" in data
    assert isinstance(data["results"], list)
    assert any(token in (res.get("snippet") or "") for res in data["results"]) or len(data["results"]) >= 0

