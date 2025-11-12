from __future__ import annotations

"""
Single source of truth for the local trio model assignments.

Other modules should import `local_trio` from here.
"""

# Local Trio v5 (Phase 3.7 - Hybrid Brain Upgrade)
# Optimized for 8GB VRAM / 32GB RAM (Alienware m18 R2)
local_trio = {
    "strategist": "qwen2:1.5b-instruct-q4_K_M",  # Qwen 2 1.5B Instruct Q4 - optimized reasoning
    "memory": "mistral:7b-instruct-v0.3-q4_K_M",  # Mistral 7B Instruct v0.3 Q4 - contextual synthesis
    "executor": "phi3:mini",   # Phi-3 Mini 3.8B Q4 - code execution
}


def as_registry() -> dict:
    """Return a structured registry dict for UI/analytics.

    This mirrors the requested JSON shape so callers can serialize directly.
    """
    return {
        "trio": {
            "strategist": {"model": local_trio["strategist"], "purpose": "reasoning", "vram_mb": 900},
            "memory": {"model": local_trio["memory"], "purpose": "summaries", "vram_mb": 4200},
            "executor": {"model": local_trio["executor"], "purpose": "actions", "vram_mb": 2400},
        },
        "total_vram_mb": 7500,
        "phase": "v3.7.0-hybrid-brain-initialization"
    }

