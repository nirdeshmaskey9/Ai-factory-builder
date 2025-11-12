from __future__ import annotations

import re
from typing import List, Dict

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_KEY_RE = re.compile(r"sk-[A-Za-z0-9\-_]{20,}")


def redact(text: str) -> str:
    s = text or ""
    s = _EMAIL_RE.sub("***@***", s)
    s = _KEY_RE.sub("sk-***REDACTED***", s)
    return s


def select_safe_snippets(entries: List[Dict], k: int) -> List[str]:
    # naive top-k by recency if available
    rows = list(entries or [])
    try:
        rows.sort(key=lambda r: r.get("created_at") or "", reverse=True)
    except Exception:
        pass
    out: List[str] = []
    for r in rows[: max(0, int(k or 0))]:
        s = (r.get("summary") or r.get("goal") or "")
        out.append(redact(str(s)))
    return out

