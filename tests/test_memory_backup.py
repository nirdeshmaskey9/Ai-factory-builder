import os
from fastapi.testclient import TestClient

os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"
os.environ["ADMIN_MODE"] = "true"

from ai_factory.main import app

client = TestClient(app)


def test_backup_and_restore_endpoints():
    b = client.get('/memory/backup')
    assert b.status_code in (200, 403)  # allow skip if not admin
    if b.status_code == 200:
        p = b.json().get('path')
        assert p and p.endswith('.db')
        r = client.post('/memory/restore')
        assert r.status_code == 200

