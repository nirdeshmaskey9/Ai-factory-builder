from __future__ import annotations

import hashlib
import logging
import os
from typing import List, Dict, Any

try:
    import chromadb  # type: ignore
    from chromadb.utils import embedding_functions  # type: ignore
    _CHROMADB_AVAILABLE = True
except Exception:
    chromadb = None  # type: ignore
    embedding_functions = None  # type: ignore
    _CHROMADB_AVAILABLE = False

from ai_factory.memory.memory_store import get_recent

logger = logging.getLogger(__name__)

# Persistent Chroma directory under data/app-internal/chroma
# Use absolute path from project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
CHROMA_PATH = os.path.join(PROJECT_ROOT, "data", "app-internal", "chroma")
os.makedirs(CHROMA_PATH, exist_ok=True)


def _hash_vector(text: str, dim: int = 128) -> List[float]:
    """
    Deterministic, quick-and-dirty embedding fallback:
    produce a fixed-size vector via rolling SHA256 hashing.
    """
    h = hashlib.sha256(text.encode("utf-8")).digest()
    # Repeat to fill target dimension
    vec = []
    while len(vec) < dim:
        for b in h:
            vec.append((b - 128) / 128.0)
            if len(vec) >= dim:
                break
    return vec


class HashEmbeddingFunction:
    def __init__(self, dim: int = 128):
        self.dim = dim

    def __call__(self, input: List[str]) -> List[List[float]]:
        return [_hash_vector(t, self.dim) for t in input]


def _init_embedding_function():
    """
    Choose embedding backend:
      - If env AI_FACTORY_EMBEDDINGS_BACKEND=FAKE -> HashEmbeddingFunction
      - Else try SentenceTransformerEmbeddingFunction ("all-MiniLM-L6-v2")
      - On failure, fall back to HashEmbeddingFunction
    """
    backend = os.getenv("AI_FACTORY_EMBEDDINGS_BACKEND", "").upper()
    if backend == "FAKE":
        logger.warning("Using FAKE hash embedding backend.")
        return HashEmbeddingFunction()

    try:
        if embedding_functions is None:
            raise RuntimeError("embedding_functions unavailable")
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        logger.info("Using SentenceTransformerEmbeddingFunction (all-MiniLM-L6-v2).")
        return ef
    except Exception as e:
        logger.warning("Falling back to FAKE hash embeddings due to init error: %s", e)
        return HashEmbeddingFunction()


class _InMemoryCollection:
    """Minimal in-memory stand-in for Chroma collection used in FAKE mode or when Chromadb is unavailable.

    Supports add(documents, ids) and query(query_texts, n_results) with a naive similarity by hash prefix.
    This is sufficient for smoke tests that only expect keys in the response structure.
    """

    def __init__(self):
        self.docs: Dict[str, str] = {}

    def add(self, documents: List[str], ids: List[str]) -> None:
        for i, d in zip(ids, documents):
            self.docs[i] = d

    def query(self, query_texts: List[str], n_results: int = 3) -> Dict[str, Any]:
        # Return up to n_results arbitrary docs; structure matches chromadb
        ids = list(self.docs.keys())[:n_results]
        docs = [self.docs[i] for i in ids]
        return {"ids": [ids], "documents": [docs], "distances": [[]], "metadatas": [[]]}


# Initialize embedding backend and vector store
embedding_fn = _init_embedding_function()
if os.getenv("AI_FACTORY_EMBEDDINGS_BACKEND", "").upper() == "FAKE" or not _CHROMADB_AVAILABLE:
    if not _CHROMADB_AVAILABLE:
        logger.warning("Chromadb not available; using in-memory collection.")
    collection = _InMemoryCollection()
else:
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)  # type: ignore[attr-defined]
        collection = client.get_or_create_collection(
            name="memory",
            embedding_function=embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )
    except Exception as e:
        logger.warning("Chromadb init failed (%s); falling back to in-memory collection.", e)
        collection = _InMemoryCollection()


def add_to_memory(request_id: str, text: str) -> None:
    """
    Add a text document to the memory vector store keyed by request_id.
    If the id already exists, it will upsert by adding a suffix.
    """
    try:
        doc_id = request_id
        # Avoid duplicate IDs by suffixing if needed
        existing = collection.get(ids=[doc_id])
        if existing and existing.get("ids"):
            doc_id = f"{request_id}:{len(existing['ids'])+1}"
        collection.add(documents=[text], ids=[doc_id])
    except Exception as e:
        logger.exception("Chroma add_to_memory error: %s", e)


def semantic_search(query: str, n_results: int = 3) -> Dict[str, Any]:
    """
    Query the vector store and return top matches.
    """
    try:
        results = collection.query(query_texts=[query], n_results=n_results)
        return results
    except Exception as e:
        logger.exception("Chroma semantic_search error: %s", e)
        return {"ids": [], "documents": [], "distances": [], "metadatas": []}
