from fastapi.testclient import TestClient
from ai_factory.main import app


client = TestClient(app)


def test_assets_present():
    for path in [
        "/static/js/chat_hooks.js",
        "/static/css/neo.css",
        "/static/img/jojo-pup.svg",
    ]:
        r = client.get(path)
        assert r.status_code == 200, path

