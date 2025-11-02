from fastapi.testclient import TestClient
from ai_factory.main import app


client = TestClient(app)


def test_ui_system_status_payload():
    r = client.get('/ui/system_status')
    assert r.status_code == 200
    j = r.json()
    for k in ('version','milestone','bridge_mode','trio_health'):
        assert k in j
    assert j['bridge_mode'] == 'hybrid'

