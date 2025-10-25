import os
from fastapi.testclient import TestClient

os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app

client = TestClient(app)


def test_ranked_search_orders_results_reasonably():
    client.post('/memory/store', json={"goal":"Build FastAPI","summary":"web","tags":["fastapi","web"]})
    client.post('/memory/store', json={"goal":"Write CLI","summary":"cli","tags":["cli"]})
    r = client.get('/memory/search', params={"q":"fastapi web", "limit": 5})
    assert r.status_code == 200
    res = r.json().get('results', [])
    assert isinstance(res, list) and len(res) >= 1
    # First result should mention fastapi or web
    top = res[0]
    text = (top.get('goal','') + ' ' + top.get('summary','')).lower()
    assert ('fastapi' in text) or ('web' in text)

