from fastapi.testclient import TestClient
from ai_factory.main import app


client = TestClient(app)


def test_memory_peek_page_and_static_assets():
    r = client.get('/ui/memory_peek')
    assert r.status_code == 200
    # Static assets should load
    for path in [
        '/static/css/neo.css',
        '/static/js/theme.js',
        '/static/js/commands.js',
        '/static/js/memory_peek.js',
        '/static/js/profile.js',
        '/static/js/voice.js',
    ]:
        resp = client.get(path)
        assert resp.status_code == 200


def test_user_snapshot_get_post():
    get1 = client.get('/ui/user_snapshot')
    assert get1.status_code == 200
    up = client.post('/ui/user_snapshot', json={"name": "Tester", "mood": "neutral", "focus": "proj", "timezone": "UTC"})
    assert up.status_code == 200
    get2 = client.get('/ui/user_snapshot')
    assert get2.status_code == 200

