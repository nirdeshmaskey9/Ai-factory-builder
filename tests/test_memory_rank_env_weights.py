import os
from fastapi.testclient import TestClient

# Heavily favor tag matching
os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"
os.environ["AI_FACTORY_MEMORY_WEIGHT_SEMANTIC"] = "0.0"
os.environ["AI_FACTORY_MEMORY_WEIGHT_TAG"] = "1.0"
os.environ["AI_FACTORY_MEMORY_WEIGHT_RECENCY"] = "0.0"

from ai_factory.main import app

client = TestClient(app)


def test_env_overrides_influence_ranking_by_tags():
    # Create two entries; only one has matching tag
    client.post('/memory/store', json={"goal":"Web App","summary":"build app","tags":["web"]})
    client.post('/memory/store', json={"goal":"CLI Tool","summary":"command line","tags":["cli"]})
    r = client.get('/memory/search', params={"q":"cli", "limit": 5})
    assert r.status_code == 200
    res = r.json().get('results', [])
    assert isinstance(res, list) and len(res) >= 1
    top = res[0]
    text = (top.get('goal','') + ' ' + top.get('summary','') + ' ' + str(top.get('tags',''))).lower()
    assert 'cli' in text

