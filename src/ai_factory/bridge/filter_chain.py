"""
Filter Chain for Clean Hybrid Output
Removes internal noise, prefixes, and debug information from hybrid responses.
"""

from __future__ import annotations

import re
from typing import Dict, Any, List, Optional


def clean_hybrid_output(hybrid_result: Dict[str, Any]) -> str:
    """
    Clean hybrid output by removing:
    - [Local] and [External] prefixes
    - Memory chunk dumps
    - Internal log traces
    - Raw trace printing
    - Previous logs
    
    Returns only the final clean assistant message.
    """
    if not hybrid_result:
        return ""
    
    # Extract the main response text
    response_text = hybrid_result.get("response_text", "")
    if not response_text:
        return ""
    
    # Remove [Local] and [External] prefixes
    response_text = re.sub(r'\[Local\]\s*', '', response_text)
    response_text = re.sub(r'\[External\]\s*', '', response_text)
    response_text = re.sub(r'\[LOCAL\]\s*', '', response_text)
    response_text = re.sub(r'\[EXTERNAL\]\s*', '', response_text)
    
    # Remove memory chunk references
    response_text = re.sub(r'Memory chunk \d+:', '', response_text, flags=re.IGNORECASE)
    response_text = re.sub(r'Chunk \d+:', '', response_text, flags=re.IGNORECASE)
    response_text = re.sub(r'Memory ID \d+', '', response_text, flags=re.IGNORECASE)
    
    # Remove RAG score displays
    response_text = re.sub(r'RAG score:[\s\d.]+', '', response_text, flags=re.IGNORECASE)
    response_text = re.sub(r'Score:[\s\d.]+', '', response_text, flags=re.IGNORECASE)
    
    # Remove advisor noise
    response_text = re.sub(r'Advisor decision:.*', '', response_text, flags=re.IGNORECASE)
    response_text = re.sub(r'Routing to:.*', '', response_text, flags=re.IGNORECASE)
    
    # Remove model think logs
    response_text = re.sub(r'Model think:.*', '', response_text, flags=re.IGNORECASE)
    response_text = re.sub(r'Thinking:.*', '', response_text, flags=re.IGNORECASE)
    
    # Remove raw hybrid_output fields if they appear in text
    response_text = re.sub(r'hybrid_output:\s*\{[^}]+\}', '', response_text)
    
    # Remove memory query traces
    response_text = re.sub(r'Memory query:.*', '', response_text, flags=re.IGNORECASE)
    response_text = re.sub(r'Query:.*', '', response_text, flags=re.IGNORECASE)
    
    # Remove chunk preview markers
    response_text = re.sub(r'--- Chunk Preview ---', '', response_text)
    response_text = re.sub(r'===.*===', '', response_text)
    
    # Remove multiple consecutive newlines
    response_text = re.sub(r'\n{3,}', '\n\n', response_text)
    
    # Remove leading/trailing whitespace
    response_text = response_text.strip()
    
    # If we have multiple paragraphs, take the last meaningful one (usually the final answer)
    paragraphs = [p.strip() for p in response_text.split('\n\n') if p.strip()]
    if paragraphs:
        # Prefer longer paragraphs (usually the actual response)
        paragraphs.sort(key=len, reverse=True)
        response_text = paragraphs[0]
    
    return response_text


def filter_memory_chunks(text: str) -> str:
    """Remove memory chunk references from text."""
    # Remove memory block patterns
    text = re.sub(r'\[Memory Block \d+\]', '', text)
    text = re.sub(r'Block \d+:', '', text)
    text = re.sub(r'Memory \d+:', '', text)
    return text.strip()


def clean_output(text: str) -> str:
    """
    Final clean filter that removes all internal noise from text output.
    This MUST be applied at the very end of the chain, after hybrid enrichment.
    Enforces brutal final clean to remove transcript spam and duplicates.
    """
    if not text:
        return ""
    
    # Remove JoJo unified reasoning prefix
    text = re.sub(r"JoJo['']s unified reasoning:\s*", "", text, flags=re.IGNORECASE)
    
    # Remove all [Local], [External]
    text = re.sub(r"\[(Local|External)\]", "", text, flags=re.IGNORECASE)
    
    # Remove memory IDs like [3648]
    text = re.sub(r"\[\d+\]", "", text)
    
    # Remove "User: ..." transcript echoes completely
    text = re.sub(r"User:\s?.*?\?", "", text)
    
    # Remove any repeated "User:" patterns
    text = re.sub(r"User:\s*", "", text)
    
    # Remove leftover metadata in brackets
    text = re.sub(r"\[[^\]]*\]", "", text)
    
    # Collapse duplicated sentences
    sentences = text.split(".")
    seen = set()
    unique = []
    for s in sentences:
        s = s.strip()
        if s and s not in seen:
            seen.add(s)
            unique.append(s)
    text = ". ".join(unique)
    
    # Collapse extra whitespace
    text = re.sub(r"\s+", " ", text).strip()
    
    return text


def filter_output(text: str) -> str:
    """
    Robust filter function that removes all internal noise from text output.
    This is the primary function used to clean assistant responses.
    """
    if not text:
        return ""
    
    # Remove [Local], [External] prefixes (case-insensitive)
    text = re.sub(r"\[(Local|External)\]", "", text, flags=re.IGNORECASE)
    
    # Remove memory chunk IDs like [3597] or [123]
    text = re.sub(r"\[\d+\]", "", text)
    
    # Remove "Summarize this: ..." patterns
    text = re.sub(r"Summarize this:.*?\.\.", "", text, flags=re.DOTALL)
    
    # Remove "my openai key is ..." patterns (privacy cleanup)
    text = re.sub(r"my openai key.*?Docs\.", "", text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove memory chunk references
    text = re.sub(r'Memory chunk \d+:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Chunk \d+:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Memory ID \d+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[Memory Block \d+\]', '', text)
    text = re.sub(r'Block \d+:', '', text)
    text = re.sub(r'Memory \d+:', '', text)
    
    # Remove RAG score displays
    text = re.sub(r'RAG score:[\s\d.]+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Score:[\s\d.]+', '', text, flags=re.IGNORECASE)
    
    # Remove advisor noise
    text = re.sub(r'Advisor decision:.*', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'Routing to:.*', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove model think logs
    text = re.sub(r'Model think:.*', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'Thinking:.*', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove raw hybrid_output fields
    text = re.sub(r'hybrid_output:\s*\{[^}]+\}', '', text)
    
    # Remove memory query traces
    text = re.sub(r'Memory query:.*', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'Query:.*', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove chunk preview markers
    text = re.sub(r'--- Chunk Preview ---', '', text)
    text = re.sub(r'===.*===', '', text)
    
    # Collapse repeated whitespace
    text = re.sub(r"\s+", " ", text)
    
    # Remove multiple consecutive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def clean_for_display(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean entire result dict for UI display.
    Removes internal fields and cleans response_text.
    """
    cleaned = result.copy()
    
    # Clean the response text
    if "response_text" in cleaned:
        cleaned["response_text"] = clean_hybrid_output(cleaned)
    
    # Remove internal debug fields
    internal_fields = [
        "hybrid_output",
        "local_trace",
        "external_trace",
        "memory_chunks",
        "rag_scores",
        "advisor_decision",
        "model_think",
        "internal_logs",
    ]
    for field in internal_fields:
        cleaned.pop(field, None)
    
    return cleaned

