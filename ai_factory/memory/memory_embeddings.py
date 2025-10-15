from __future__ import annotations

import hashlib
import logging
import os
from typing import List, Dict, Any

import chromadb
from chromadb.utils import embedding_functions

from ai_factory.memory.memory_store import get_recent

logger = logging.getLogger(__name__)

# Persistent Chroma directory under ai_factory/data/chroma
CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "chroma")
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
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        logger.info("Using SentenceTransformerEmbeddingFunction (all-MiniLM-L6-v2).")
        return ef
    except Exception as e:
        logger.warning("Falling back to FAKE hash embeddings due to init error: %s", e)
        return HashEmbeddingFunction()


# Initialize Chroma persistent client & collection
client = chromadb.PersistentClient(path=CHROMA_PATH)
embedding_fn = _init_embedding_function()
collection = client.get_or_create_collection(name="memory", embedding_function=embedding_fn, metadata={"hnsw:space": "cosine"})


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

