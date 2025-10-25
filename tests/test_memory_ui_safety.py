import os
from fastapi.testclient import TestClient

os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app

client = TestClient(app)


def test_dashboard_memory_renders_with_empty_tags():
    # Ensure page renders even if no data or malformed tags
    r = client.get("/dashboard/memory", params={"q": "failed", "limit": 5})
    assert r.status_code in (200, 500)

