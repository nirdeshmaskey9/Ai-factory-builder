from fastapi.testclient import TestClient
from ai_factory.main import app


client = TestClient(app)


def test_persona_persist():
    r = client.post('/ui/control_state', json={'persona_mode': 'analyst'})
    assert r.status_code == 200
    r2 = client.get('/ui/control_state').json()
    assert r2.get('persona_mode') == 'analyst'


def test_dialogue_recent_and_close():
    # Ensure close works and recent returns a list for 'current'
    r1 = client.post('/dialogue/close?dry-run=true')
    assert r1.status_code == 200
    r2 = client.get('/dialogue/recent?session=current&n=5')
    assert r2.status_code == 200
    assert isinstance(r2.json(), list)

