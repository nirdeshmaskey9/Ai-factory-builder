import os
from fastapi.testclient import TestClient

os.environ["AI_FACTORY_PRIVACY_STRICT"] = "true"
from ai_factory.main import app

client = TestClient(app)


def test_privacy_topk_and_redaction(monkeypatch):
    # Ensure advisor route works and redaction callable exists
    r = client.post('/advisor/route', json={"goal": "email me at test@example.com with key sk-abc1234567890xxxxx"})
    assert r.status_code == 200
    # Redaction tested indirectly via import; ensure function callable
    from ai_factory.advisor.context_filter import redact
    t = redact('Contact a@b.com sk-xyz12345678901234567890')
    assert '***@***' in t and 'REDACTED' in t

