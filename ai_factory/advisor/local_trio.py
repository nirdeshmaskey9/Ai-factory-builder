from __future__ import annotations

"""
Single source of truth for the local trio model assignments.

Other modules should import `local_trio` from here.
"""

# Local Trio v4 (Phase 3.9)
local_trio = {
    "strategist": "phi3:medium",
    "memory": "mistral",
    "executor": "phi3:mini",
}


def as_registry() -> dict:
    """Return a structured registry dict for UI/analytics.

    This mirrors the requested JSON shape so callers can serialize directly.
    """
    return {
        "trio": {
            "strategist": {"model": local_trio["strategist"], "purpose": "reasoning"},
            "memory": {"model": local_trio["memory"], "purpose": "summaries"},
            "executor": {"model": local_trio["executor"], "purpose": "actions"},
        }
    }

