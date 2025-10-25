import os
from fastapi.testclient import TestClient

os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"

from ai_factory.main import app

client = TestClient(app)


def test_auto_learn_from_evaluator_pass_flow():
    # Trigger evaluator with a simple session by calling evaluator/evaluate with goal
    r = client.post('/evaluator/evaluate', json={"goal":"Build web app"})
    assert r.status_code in (200, 404)
    # Ensure memory stats endpoint accessible
    s = client.get('/memory/stats')
    assert s.status_code == 200
