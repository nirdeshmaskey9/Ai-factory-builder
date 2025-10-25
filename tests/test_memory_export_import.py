import os, json
from fastapi.testclient import TestClient

os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app

client = TestClient(app)


def test_export_and_import_cycle():
    client.post('/memory/store', json={"goal":"Exportable","summary":"S","tags":["x"],"score":0.1})
    r = client.get('/memory/export', params={"fmt":"json"})
    assert r.status_code == 200
    path = r.json().get('path')
    assert path and path.endswith('.json')
    # Load exported and import back (should dedupe by goal+tags)
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    r2 = client.post('/memory/import', json={"items": data})
    assert r2.status_code == 200

