from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from pathlib import Path

from .rag_service import ingest_document, retrieve


router = APIRouter(prefix="/rag", tags=["RAG"])


class LoadIn(BaseModel):
    path: str
    tags: List[str] | None = None


class QueryIn(BaseModel):
    query: str
    top_k: int = 5


@router.get("/status")
def rag_status() -> Dict[str, Any]:
    base = Path("data/vector_db")
    exists = base.exists()
    idx = (base / "index.faiss").exists()
    doc = (base / "docs.txt").exists()
    return {
        "path": str(base),
        "exists": exists,
        "index": idx,
        "docs": doc,
    }


@router.post("/load")
def rag_load(payload: LoadIn) -> Dict[str, Any]:
    p = payload.path
    if not Path(p).exists():
        raise HTTPException(status_code=404, detail="file not found")
    res = ingest_document(p, tags=list(payload.tags or []))
    return {"status": "ok", **res}


@router.post("/query")
def rag_query(payload: QueryIn) -> Dict[str, Any]:
    out = retrieve(payload.query, top_k=payload.top_k)
    return {"results": out}

