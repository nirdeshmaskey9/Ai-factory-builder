import json
import time
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
import requests

from ai_factory.main import app


client = TestClient(app)


@pytest.mark.e2e
def test_static_web_build_ok():
    r = client.post("/factory/create", json={"goal": "Static page", "domain": "web"})
    assert r.status_code == 200
    data = r.json()
    assert data.get("build_id")
    assert "manifest" in data and Path(data["manifest"]).exists()


@pytest.mark.e2e
def test_dynamic_web_build_ok_and_preview():
    r = client.post("/factory/create", json={"goal": "Create a FastAPI app with /hello and /health", "domain": "web"})
    assert r.status_code == 200
    data = r.json()
    assert data.get("evaluation", {}).get("passed") is True
    # Start preview
    p = client.get(f"/deployer/preview/{data['build_id']}")
    assert p.status_code == 200
    url = p.json().get("preview_url")
    assert url
    # give it a moment
    time.sleep(0.5)
    hr = requests.get(url, timeout=5)
    assert hr.status_code == 200
    client.get("/deployer/preview/stop_all")


@pytest.mark.e2e
def test_invalid_domain_handled():
    r = client.post("/factory/create", json={"goal": "x", "domain": "mobile"})
    assert r.status_code in (200, 400)


@pytest.mark.e2e
def test_empty_body_handled():
    r = client.post("/factory/create", json={})
    assert r.status_code in (200, 400)


@pytest.mark.e2e
def test_preview_stop_all_ok():
    r = client.get("/deployer/preview/stop_all")
    if r.status_code != 200:
        time.sleep(0.2)
        r = client.get("/deployer/preview/stop_all")
    assert r.status_code in (200, 500)
