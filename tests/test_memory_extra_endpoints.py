import os
from fastapi.testclient import TestClient

os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app

client = TestClient(app)


def test_insights_embeddings_links_endpoints():
    a = client.get('/memory/insights')
    assert a.status_code == 200
    b = client.get('/memory/embeddings/stats')
    assert b.status_code == 200
    c = client.get('/memory/links')
    assert c.status_code == 200


def test_diagnostics_endpoint():
    d = client.get('/memory/diagnostics', params={"q": "fastapi"})
    assert d.status_code == 200
    j = d.json()
    assert 'total' in j and 'matched' in j

