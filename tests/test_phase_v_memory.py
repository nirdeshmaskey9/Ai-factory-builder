from fastapi.testclient import TestClient
from ai_factory.main import app


client = TestClient(app)


def test_dialogue_recent_and_close_routes():
    r = client.get('/dialogue/recent?session=test&n=2')
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    r2 = client.post('/dialogue/close?session=test&dry-run=true')
    assert r2.status_code == 200
    j = r2.json()
    for k in ['topic','key_facts','tone','decisions','todos']:
        assert k in j


def test_persona_mode_persists_and_prefix():
    # Set persona to analyst
    s = client.post('/ui/control_state', json={'persona_mode': 'analyst'})
    assert s.status_code == 200
    # Verify
    g = client.get('/ui/control_state').json()
    assert g.get('persona_mode') == 'analyst'
    # Send a chat and expect 200; prefix injection is internal but we at least ensure route works
    r = client.post('/bridge/chat', json={'user_input': 'Estimate cost for 5 items', 'session_id': 'p1'})
    assert r.status_code == 200


def test_mood_logged_after_message():
    # Send message that implies stress
    r = client.post('/bridge/chat', json={'user_input': 'I feel stressed about deadline', 'session_id': 'm1'})
    assert r.status_code == 200
    # No direct read, but ensure recent turns returns entries
    recent = client.get('/dialogue/recent?session=m1&n=5').json()
    assert isinstance(recent, list)
    assert len(recent) >= 1

