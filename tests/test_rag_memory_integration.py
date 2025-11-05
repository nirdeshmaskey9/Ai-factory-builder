from __future__ import annotations

import os
from pathlib import Path
from fastapi.testclient import TestClient

from ai_factory.main import app
from ai_factory.rag.rag_service import ingest_document, retrieve
from ai_factory.memory.memory_mcp import record_feedback


def test_ingest_and_retrieve(tmp_path: Path):
    p = tmp_path / "doc.txt"
    p.write_text("JoJo is a helpful AI assistant that loves RAG.", encoding="utf-8")

    res = ingest_document(str(p))
    assert res.get("chunks", 0) >= 1

    hits = retrieve("Who loves RAG?", top_k=3)
    assert isinstance(hits, list)
    assert len(hits) >= 1


def test_feedback_log_written(tmp_path: Path):
    # Point data dir to a temp location for isolation
    data_dir = tmp_path / "data" / "memory"
    os.makedirs(data_dir, exist_ok=True)
    # Monkeypatch FEEDBACK_PATH via environment by changing CWD
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        record_feedback("auto_eval", 5, "Great answer", {"query": "test"})
        p = Path("data/memory/feedback_log.json")
        assert p.exists()
        txt = p.read_text(encoding="utf-8")
        assert "Great answer" in txt
    finally:
        os.chdir(old_cwd)


def test_rag_routes_status_and_query(tmp_path: Path):
    # Prepare a document and POST to /rag/load
    d = tmp_path / "doc2.txt"
    d.write_text("RAG testing document. JoJo reads local files.", encoding="utf-8")
    client = TestClient(app)
    r1 = client.post("/rag/load", json={"path": str(d)})
    assert r1.status_code == 200

    rstatus = client.get("/rag/status")
    assert rstatus.status_code == 200

    r2 = client.post("/rag/query", json={"query": "Who reads local files?", "top_k": 5})
    assert r2.status_code == 200
    body = r2.json()
    assert isinstance(body.get("results"), list)
    assert len(body.get("results")) >= 1

