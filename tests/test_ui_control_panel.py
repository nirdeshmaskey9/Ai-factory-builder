from fastapi.testclient import TestClient
from ai_factory.main import app


client = TestClient(app)


def test_toggle_and_usage():
    r1 = client.get('/ui/control_state')
    assert r1.status_code == 200
    s1 = r1.json()
    r2 = client.post('/ui/toggle_mock')
    assert r2.status_code == 200
    s2 = client.get('/ui/control_state').json()
    assert s1['mock_mode'] != s2['mock_mode']

