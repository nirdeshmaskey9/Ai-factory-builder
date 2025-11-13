"""
JoJo Phase 4 - Awareness Layer
Provides self-awareness, identity awareness, and user state awareness.
"""

from ai_factory.awareness.awareness_engine import (
    AwarenessContext,
    get_self_awareness,
    get_purpose_awareness,
    get_creator_awareness,
    get_user_awareness,
    build_awareness_context,
    get_awareness_prompt_injection,
    get_awareness_summary_for_logs,
)

__all__ = [
    "AwarenessContext",
    "get_self_awareness",
    "get_purpose_awareness",
    "get_creator_awareness",
    "get_user_awareness",
    "build_awareness_context",
    "get_awareness_prompt_injection",
    "get_awareness_summary_for_logs",
]

