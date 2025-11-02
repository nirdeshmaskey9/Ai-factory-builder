from fastapi.testclient import TestClient
from ai_factory.main import app
import json


client = TestClient(app)


def test_ui_chat_websocket_three_turns():
    with client.websocket_connect('/ws/chat') as ws:
        # Greeting
        msg = json.loads(ws.receive_text())
        assert msg.get('role') == 'assistant'
        # Three turns
        turns = 0
        for i in range(3):
            ws.send_text(json.dumps({"user_input": f"Hello {i}"}))
            # Expect two frames: echo(user) + assistant
            echo = json.loads(ws.receive_text())
            asst = json.loads(ws.receive_text())
            assert echo.get('role') == 'user'
            assert asst.get('role') == 'assistant'
            assert isinstance(asst.get('content'), str) and len(asst.get('content')) >= 0
            turns += 1
        assert turns == 3

