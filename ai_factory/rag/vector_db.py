from __future__ import annotations

from pathlib import Path
from typing import Tuple, List, Optional


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def build_or_load_index(emb_model, path: str = "data/vector_db"):
    """Create or load the FAISS index and doc store.

    Stores:
    - index at `{path}/index.faiss`
    - docstore (list[str]) at `{path}/docs.txt` (\u0001-separated)
    - metadata (list[dict]) at `{path}/meta.json`
    """
    import json
    try:
        import faiss  # type: ignore
    except Exception as e:
        raise RuntimeError("faiss not available; install faiss-cpu") from e

    base = Path(path)
    _ensure_dir(base)
    idx_path = base / "index.faiss"
    docs_path = base / "docs.txt"
    meta_path = base / "meta.json"

    index = None
    docs: List[str] = []
    meta: List[dict] = []

    if idx_path.exists() and docs_path.exists() and meta_path.exists():
        index = faiss.read_index(str(idx_path))
        try:
            raw = docs_path.read_text(encoding="utf-8")
            docs = raw.split("\u0001") if raw else []
        except Exception:
            docs = []
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            meta = [{} for _ in docs]
    else:
        # Build a new, empty index matching embedding dim
        import numpy as np
        dim = emb_model.get_sentence_embedding_dimension()
        index = faiss.IndexFlatIP(dim)
        faiss.write_index(index, str(idx_path))
        docs_path.write_text("", encoding="utf-8")
        meta_path.write_text("[]", encoding="utf-8")

    return index, docs, meta, (idx_path, docs_path, meta_path)


def persist(index, files: Tuple[Path, Path, Path], docs: List[str], meta: List[dict]) -> None:
    import json
    import faiss  # type: ignore
    idx_path, docs_path, meta_path = files
    faiss.write_index(index, str(idx_path))
    docs_path.write_text("\u0001".join(docs), encoding="utf-8")
    meta_path.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")


def search(index, query_vec, top_k: int = 5) -> Tuple[List[int], List[float]]:
    import numpy as np
    if not isinstance(query_vec, np.ndarray):
        import numpy as _np
        query_vec = _np.array([query_vec])
    if query_vec.ndim == 1:
        query_vec = query_vec.reshape(1, -1)
    # Normalize for cosine similarity via inner product
    norms = (query_vec ** 2).sum(axis=1, keepdims=True) ** 0.5
    query_vec = query_vec / (norms + 1e-12)
    D, I = index.search(query_vec, top_k)
    return I[0].tolist(), D[0].tolist()

