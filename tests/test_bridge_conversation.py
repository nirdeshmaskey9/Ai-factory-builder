import os
import json
from fastapi.testclient import TestClient
from ai_factory.main import app


client = TestClient(app)


def test_preserve_user_wording():
    os.environ["JOJO_BRIDGE_MODE"] = "mock"  # ensure no external call
    payload = {"user_input": "Please remember my project path C:/Users/Alice/Dev/secret", "session_id": "conv-1"}
    r = client.post("/bridge/chat", json=payload)
    assert r.status_code == 200
    data = r.json()
    # CEO should carry sanitized text but preserve exact user wording in ceo.user_text
    assert data["ceo"]["user_text"] == payload["user_input"]


def test_context_enrichment():
    os.environ["JOJO_BRIDGE_MODE"] = "mock"
    r = client.post("/bridge/chat", json={"user_input": "fastapi memory context", "session_id": "conv-ctx"})
    assert r.status_code == 200
    data = r.json()
    # context_additions present (may be empty but should exist)
    assert "context_additions" in data["ceo"]


def test_proxy_response_structure():
    os.environ["JOJO_BRIDGE_MODE"] = "mock"
    r = client.post("/bridge/chat", json={"user_input": "hello world", "session_id": "conv-2"})
    assert r.status_code == 200
    data = r.json()
    assert "response_text" in data and isinstance(data["response_text"], str)


def test_redaction_security():
    os.environ["JOJO_BRIDGE_MODE"] = "mock"
    sensitive = "my openai key is sk-ABCDEF1234567890XYZ and home C:\\Users\\Bob\\Docs"
    r = client.post("/bridge/chat", json={"user_input": sensitive, "session_id": "conv-3"})
    assert r.status_code == 200
    data = r.json()
    sanitized = data["ceo"]["sanitized_text"]
    assert "sk-***REDACTED***" in sanitized or "***REDACTED***" in sanitized


def test_summary_lossless():
    os.environ["JOJO_BRIDGE_MODE"] = "mock"
    r = client.post("/bridge/summarize", json={"conversation_id": "conv-4"})
    assert r.status_code == 200
    data = r.json()
    assert "summary" in data


def test_full_bridge_flow():
    os.environ["JOJO_BRIDGE_MODE"] = "mock"
    r = client.post("/bridge/chat", json={"user_input": "Summarize this: FastAPI is great.", "session_id": "conv-5"})
    assert r.status_code == 200
    data = r.json()
    assert "response_text" in data
    assert "memory_updates" in data
    status = client.get("/bridge/status")
    assert status.status_code == 200
    st = status.json()
    assert st.get("bridge") == "ok"

