from pathlib import Path

def _read_version() -> str:
    try:
        p = Path(__file__).resolve().parent.parent / "VERSION"
    except Exception:
        return "0.0.0"
    if p.exists():
        try:
            return p.read_text(encoding="utf-8").strip()
        except Exception:
            return "0.0.0"
    return "0.0.0"

__version__ = _read_version()
__all__ = ["main", "__version__"]
