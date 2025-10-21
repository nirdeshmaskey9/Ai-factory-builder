from __future__ import annotations

from pathlib import Path
from typing import Any


def create_env(template_root: Path) -> Any:
    """Create a Jinja2 environment lazily.

    Imports Jinja2 inside the function to avoid hard dependency at import time.
    """
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape  # type: ignore
    except ModuleNotFoundError as e:
        raise RuntimeError(
            "Jinja2 is required for template rendering. Please install 'jinja2'."
        ) from e
    loader = FileSystemLoader(str(template_root))
    env = Environment(loader=loader, autoescape=select_autoescape(["html", "xml", "j2"]))
    return env
