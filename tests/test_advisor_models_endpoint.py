from fastapi.testclient import TestClient
from ai_factory.main import app

client = TestClient(app)


def test_advisor_models_endpoint_lists_trio():
    r = client.get('/advisor/models')
    assert r.status_code == 200
    j = r.json()
    assert isinstance(j.get('locals'), list) and len(j['locals']) == 3

