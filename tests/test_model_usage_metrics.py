from fastapi.testclient import TestClient
from ai_factory.main import app

client = TestClient(app)


def test_model_usage_aggregation():
    # Trigger a planner call via planner dispatch
    r = client.post('/planner/dispatch', json={"task_type": "coding", "prompt": "plan something"})
    assert r.status_code in (200, 400)
    # Now query analytics models
    a = client.get('/analytics/models')
    assert a.status_code == 200
    j = a.json()
    assert 'by_model' in j

