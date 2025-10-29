import os
from fastapi.testclient import TestClient

os.environ["AI_FACTORY_EMBEDDINGS_BACKEND"] = "FAKE"
os.environ["ADMIN_MODE"] = "true"

from ai_factory.main import app

client = TestClient(app)


def test_memory_admin_buttons_and_endpoints():
    # Page renders and contains buttons
    r = client.get("/dashboard/memory")
    assert r.status_code == 200
    html = r.text
    for text in ["Export JSON", "Export CSV", "Import", "Backup", "Restore"]:
        assert text in html

    # Export endpoints
    ej = client.get("/memory/export", params={"fmt": "json"})
    assert ej.status_code == 200
    ec = client.get("/memory/export", params={"fmt": "csv"})
    assert ec.status_code == 200

    # Import minimal payload
    imp = client.post("/memory/import", json={"items": [{"goal": "ui-import", "summary": "from ui", "tags": "ui,import", "score": 0.1}]})
    assert imp.status_code == 200

    # Backup/Restore
    b = client.get("/memory/backup")
    assert b.status_code == 200
    r = client.post("/memory/restore")
    assert r.status_code in (200, 404)  # 404 allowed if no backup found

