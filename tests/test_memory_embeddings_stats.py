import os
from fastapi.testclient import TestClient

os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app

client = TestClient(app)


def test_embeddings_stats_keys_present():
    r = client.get('/memory/embeddings/stats')
    assert r.status_code == 200
    j = r.json()
    assert 'total_entries' in j and 'with_embeddings' in j

