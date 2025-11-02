import os
import json
import pytest
from fastapi.testclient import TestClient
from ai_factory.main import app


client = TestClient(app)


live_required = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set; skipping live verification"
)


@pytest.mark.livecheck
@live_required
def test_live_bridge_toggle_and_usage():
    # Ensure we are in live mode
    state = client.get('/ui/control_state').json()
    if state.get('mock_mode'):
        client.post('/ui/toggle_mock')
        state = client.get('/ui/control_state').json()
    assert state.get('mock_mode') is False

    # WS chat: send one turn and capture assistant reply
    with client.websocket_connect('/ws/chat') as ws:
        _greet = json.loads(ws.receive_text())
        ws.send_text(json.dumps({"user_input": "Hello, JoJo"}))
        _echo = json.loads(ws.receive_text())
        asst = json.loads(ws.receive_text())
        assert asst.get('role') == 'assistant'
        assert '[MOCK' not in (asst.get('content') or '')

    # Usage should increase in live mode
    after = client.get('/ui/control_state').json()
    assert after.get('tokens', 0) >= 0  # non-negative
    assert after.get('usd', 0.0) >= 0.0

    # Restore mock mode for safety
    if not after.get('mock_mode'):
        client.post('/ui/toggle_mock')

