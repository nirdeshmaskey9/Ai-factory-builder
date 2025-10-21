from fastapi.testclient import TestClient
from pathlib import Path
from ai_factory.main import app


def test_build_web_manifest_and_files():
    client = TestClient(app)
    r = client.post("/factory/create", json={"goal": "Landing page", "domain": "web"})
    assert r.status_code == 200
    data = r.json()
    manifest = Path(data["manifest"])
    assert manifest.exists(), "manifest missing"
    # outputs path should exist and contain at least one file
    out = Path(data.get("outputs_path"))
    assert out.exists()
    files = list(out.rglob("*"))
    assert any(p.is_file() for p in files), "no files generated"

