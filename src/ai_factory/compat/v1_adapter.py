"""Compatibility adapter from v1 blueprints to v2-like structure.

For MVP, this performs a shallow pass-through while ensuring expected keys
exist. Expand as v2 schema evolves.
"""

from __future__ import annotations

from typing import Any, Mapping


def to_v2(v1_blueprint: Mapping[str, Any]) -> dict[str, Any]:
    bp = dict(v1_blueprint)
    # Ensure minimal common fields with sane defaults
    bp.setdefault("name", bp.get("title") or "app")
    bp.setdefault("description", "Generated application")
    return bp

