from fastapi.testclient import TestClient
from ai_factory.main import app

client = TestClient(app)


def test_trio_health_endpoint_has_roles():
    r = client.get('/advisor/trio_health')
    assert r.status_code == 200
    j = r.json()
    assert 'roles' in j
    roles = j['roles']
    assert 'strategist' in roles and 'memory' in roles and 'executor' in roles

