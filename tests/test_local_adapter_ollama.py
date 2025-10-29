import httpx
import json
import pytest
from ai_factory.models.local_adapter.ollama_client import generate, LocalBackendError


class DummyResponse:
    def __init__(self, status_code=200, data=None, text='ok'):
        self.status_code = status_code
        self._data = data or {"response": "hello", "eval_count": 4, "prompt_eval_count": 3}
        self.text = text
    def json(self):
        return self._data


def test_generate_success(monkeypatch):
    def fake_post(self, url, json=None):
        return DummyResponse(200)
    monkeypatch.setattr(httpx.Client, 'post', fake_post)
    txt, lat, tin, tout = generate("http://127.0.0.1:11434", "mistral", "hi", timeout=1)
    assert isinstance(txt, str) and tin >= 0 and tout >= 0


def test_generate_http_error(monkeypatch):
    def fake_post(self, url, json=None):
        return DummyResponse(500, text='err')
    monkeypatch.setattr(httpx.Client, 'post', fake_post)
    with pytest.raises(LocalBackendError):
        generate("http://x", "m", "p")

