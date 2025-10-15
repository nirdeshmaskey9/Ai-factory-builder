from __future__ import annotations

import os
from typing import Any, Dict, List, Optional


class _Collection:
    def __init__(self, path: str, name: str, embedding_function=None):
        self.path = path
        self.name = name
        self.embedding_function = embedding_function
        self._docs: Dict[str, str] = {}

    def add(self, documents: List[str], ids: List[str]) -> None:
        for doc, _id in zip(documents, ids):
            self._docs[_id] = doc

    def get(self, ids: List[str]) -> Dict[str, Any]:
        found_ids = [_id for _id in ids if _id in self._docs]
        return {"ids": found_ids, "documents": [self._docs[_id] for _id in found_ids]}

    def query(self, query_texts: List[str], n_results: int = 3) -> Dict[str, Any]:
        # Extremely naive lexical similarity: shared token count
        results_ids: List[List[str]] = []
        results_docs: List[List[str]] = []
        results_scores: List[List[float]] = []
        tokens_docs = {k: set(v.lower().split()) for k, v in self._docs.items()}
        for q in query_texts:
            qt = set(q.lower().split())
            scored = []
            for _id, toks in tokens_docs.items():
                score = 1.0 / (1 + len(qt - toks))  # simple inverse difference
                scored.append((_id, score))
            scored.sort(key=lambda x: x[1], reverse=True)
            top = scored[:n_results]
            ids = [_id for _id, _ in top]
            docs = [self._docs[_id] for _id in ids]
            dists = [1 - s for _, s in top]
            results_ids.append(ids)
            results_docs.append(docs)
            results_scores.append(dists)
        return {"ids": results_ids, "documents": results_docs, "distances": results_scores}


class PersistentClient:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(self.path, exist_ok=True)
        self._collections: Dict[str, _Collection] = {}

    def get_or_create_collection(self, name: str, embedding_function=None, metadata: Optional[Dict[str, Any]] = None):
        if name not in self._collections:
            self._collections[name] = _Collection(self.path, name, embedding_function)
        return self._collections[name]

