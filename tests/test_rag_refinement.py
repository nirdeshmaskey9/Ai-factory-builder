from __future__ import annotations

import os
import json
from pathlib import Path
from typing import List, Dict

import pytest
from fastapi.testclient import TestClient

from ai_factory.main import app


def test_sync_with_memory_upserts(monkeypatch, tmp_path: Path):
    # Run in temp cwd so RAG data lands in tmp data/
    old = os.getcwd()
    os.chdir(tmp_path)
    try:
        # Mock recent memories
        from ai_factory import memory
        import ai_factory.rag.rag_service as rag

        def fake_recent(limit: int = 200) -> List[Dict]:
            return [
                {"id": "m1", "text": "Alpha JoJo memory", "ts": 1.0, "tags": ["t1"]},
                {"id": "m2", "text": "Beta JoJo memory", "ts": 2.0, "tags": ["t2"]},
            ]

        monkeypatch.setattr(
            rag, "get_recent_memories", fake_recent, raising=False
        )
        out = rag.sync_with_memory_mcp(limit=10)
        assert out.get("added", 0) >= 2
        # second run should skip duplicates
        out2 = rag.sync_with_memory_mcp(limit=10)
        assert out2.get("skipped", 0) >= 2
    finally:
        os.chdir(old)


def test_feedback_weighting_changes_order(monkeypatch, tmp_path: Path):
    old = os.getcwd()
    os.chdir(tmp_path)
    try:
        import ai_factory.rag.rag_service as rag
        # Ingest two texts
        d1 = tmp_path / "a.txt"
        d2 = tmp_path / "b.txt"
        t1 = "JoJo loves retrieval augmented generation."
        t2 = "Completely unrelated text block."
        d1.write_text(t1, encoding="utf-8")
        d2.write_text(t2, encoding="utf-8")
        from ai_factory.rag.rag_service import ingest_document, retrieve
        ingest_document(str(d1))
        ingest_document(str(d2))
        # Create feedback rating for the first chunk by hash
        h1 = rag._chunk_hash(t1)
        fpath = Path("data/memory/feedback_log.json")
        fpath.parent.mkdir(parents=True, exist_ok=True)
        fpath.write_text(json.dumps([
            {"event": "test", "rating": 5, "notes": "good", "context": {"chunk_hash": h1}, "ts": 0}
        ]), encoding="utf-8")
        res = retrieve("JoJo retrieval", top_k=5)
        assert len(res) >= 2
        # chunk with rating 5 should be ranked first
        assert h1 == res[0]["metadata"]["hash"]
    finally:
        os.chdir(old)


def test_retrieve_with_retry(monkeypatch, tmp_path: Path):
    import ai_factory.rag.rag_service as rag
    calls = {"n": 0, "args": []}

    def fake_retrieve(q: str, top_k: int = 5):
        calls["n"] += 1
        calls["args"].append(top_k)
        # Always return low score
        return [{"text": "x", "score": 0.1, "metadata": {}}]

    monkeypatch.setattr(rag, "retrieve", fake_retrieve, raising=True)
    out = rag.retrieve_with_retry("q", top_k=4, min_score=0.4, retry=True)
    assert calls["n"] == 2
    assert calls["args"] == [4, 7]


def test_advisor_context_preview_contains_both(monkeypatch):
    from ai_factory.advisor.advisor_service import route_task

    def fake_retrieve(q: str, top_k: int = 5):
        return [{"text": "RAG piece", "score": 0.9, "metadata": {}}]

    import ai_factory.advisor.advisor_service as adv
    monkeypatch.setattr(adv, "_rag", type("X", (), {"retrieve": staticmethod(fake_retrieve)}))

    out = route_task("test fusion", domain=None, hint=None, topk=1)
    ctx = out.get("context_preview") or {}
    assert "memory_context" in ctx and "rag_context" in ctx
    assert len((ctx.get("memory_context") or "")) <= 512
    assert len((ctx.get("rag_context") or "")) <= 512


def test_rag_node_endpoints(tmp_path: Path):
    old = os.getcwd()
    os.chdir(tmp_path)
    try:
        client = TestClient(app)
        r1 = client.get("/dashboard/rag_nodes")
        assert r1.status_code == 200
        r2 = client.post("/dashboard/rag_sync_memory")
        assert r2.status_code == 200
        r3 = client.get("/dashboard/rag_metrics")
        assert r3.status_code == 200
    finally:
        os.chdir(old)

