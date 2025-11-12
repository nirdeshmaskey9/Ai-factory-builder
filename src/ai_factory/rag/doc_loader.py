from __future__ import annotations

from pathlib import Path
from typing import List, Dict


def _make_doc(text: str, source: str, extra_meta: Dict | None = None) -> Dict:
    m = {"source": source}
    if extra_meta:
        m.update(extra_meta)
    return {"page_content": text, "metadata": m}


def load_document(path: str) -> List[Dict]:
    """Load a document and return normalized chunk list.

    Supports: .pdf, .txt, .md, .json
    Splits long text into ~800 char chunks with small overlap.
    """
    import json
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"document not found: {path}")

    suffix = p.suffix.lower()
    text = ""
    docs: List[Dict] = []

    if suffix == ".pdf":
        try:
            from pypdf import PdfReader  # type: ignore
        except Exception as e:
            raise RuntimeError("pypdf is required for PDF ingestion") from e
        reader = PdfReader(str(p))
        for i, page in enumerate(reader.pages):
            t = page.extract_text() or ""
            if t.strip():
                docs.append(_make_doc(t, str(p), {"page": i + 1, "type": "pdf"}))
        return _split_chunks(docs)
    elif suffix in (".txt", ".md"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        return _split_chunks([_make_doc(text, str(p), {"type": suffix.lstrip('.')})])
    elif suffix == ".json":
        data = json.loads(p.read_text(encoding="utf-8"))
        flat = _flatten_json(data)
        return _split_chunks([_make_doc(flat, str(p), {"type": "json"})])
    else:
        # Try plain text
        text = p.read_text(encoding="utf-8", errors="ignore")
        return _split_chunks([_make_doc(text, str(p), {"type": "text"})])


def _split_chunks(docs: List[Dict], size: int = 800, overlap: int = 80) -> List[Dict]:
    out: List[Dict] = []
    for d in docs:
        t = d.get("page_content") or ""
        m = d.get("metadata") or {}
        start = 0
        n = len(t)
        if n <= size:
            out.append({"page_content": t, "metadata": m})
            continue
        while start < n:
            end = min(n, start + size)
            chunk = t[start:end]
            out.append({"page_content": chunk, "metadata": m})
            if end == n:
                break
            start = end - overlap
            if start < 0:
                start = 0
    return out


def _flatten_json(data) -> str:
    parts: List[str] = []
    def walk(prefix: str, obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                walk(f"{prefix}.{k}" if prefix else str(k), v)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk(f"{prefix}[{i}]", v)
        else:
            parts.append(f"{prefix}: {obj}")
    walk("", data)
    return "\n".join(parts)

