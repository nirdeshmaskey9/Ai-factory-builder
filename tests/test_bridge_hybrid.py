import time
import pytest
from fastapi.testclient import TestClient
from ai_factory.main import app


client = TestClient(app)


@pytest.mark.timeout(10)
def test_bridge_phase1_mock(monkeypatch):
    """Phase 1 – fast mock bridge verification"""
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "1")
    monkeypatch.delenv("HYBRID_DIAGNOSTIC", raising=False)
    # Even if external is callable, in test mode (no diagnostic) we expect mock path
    monkeypatch.setattr("ai_factory.bridge.bridge_service.call_gpt5", lambda x: "[MOCK GPT-5 RESPONSE]")
    res = client.post(
        "/bridge/chat",
        json={"user_input": "Explain JoJo's purpose", "session_id": "test-mock"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["model"] == "hybrid"
    assert "MOCK" in data["response_text"]
    assert data.get("test_mode") is True


@pytest.mark.timeout(15)
def test_bridge_phase2_live(monkeypatch):
    """Phase 2 – real hybrid bridge verification with timeout"""
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "1")
    monkeypatch.setenv("HYBRID_DIAGNOSTIC", "1")
    t0 = time.time()
    res = client.post(
        "/bridge/chat",
        json={"user_input": "Hey JoJo, what is your purpose today?", "session_id": "test-live"},
    )
    elapsed = time.time() - t0
    assert res.status_code == 200
    data = res.json()
    assert "hybrid" in data["model"]
    assert elapsed < 15
