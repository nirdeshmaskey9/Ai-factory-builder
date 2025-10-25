import os
from fastapi.testclient import TestClient

os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app

client = TestClient(app)


def test_context_preview_route():
    # Seed two entries with a run id to preview
    run_id = 55501
    client.post('/memory/store', json={"run_id": run_id, "goal":"Build web","summary":"ok","tags":["web"]})
    client.post('/memory/store', json={"goal":"Another web","summary":"ok","tags":["web"]})
    r = client.get(f'/dashboard/memory/context/{run_id}')
    assert r.status_code == 200
    assert 'Context for Run' in r.text

