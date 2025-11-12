# Phase 3.9.2 - Unified Identity Final Cleanup + Memory Recall Fix

**Version:** v3.9.2-unified-clean-final  
**Date:** 2025-11-12T17:39:01Z  
**Phase:** 3.9.2

## Overview

This phase fixes two critical issues:
1. **Memory chunks/RAG noise leaking into chat output** - Fixed by applying final clean filter at the very end of the chain
2. **JoJo failing to recall memory** - Fixed by adding a Memory Recall Hook that injects relevant user memory into the system prompt

## Issues Fixed

### ISSUE 1 — Memory chunks / RAG noise leaking into chat output

**Symptoms:**
- "JoJo's unified reasoning: …" appears in output
- `[Local]`, `[External]`, `[3591]`, `[3630]`, etc. appear
- Old memory like "my openai key…", "hello world" etc. appear
- Repeated "who are you?" tokens
- JoJo mixes reasoning tokens into the final output

**Root Cause:**
- `clean_output()` was applied too early in the chain
- It MUST be applied after hybrid enrichment

**Fix:**
- Added `clean_output()` function to `filter_chain.py` with specific pattern matching
- Applied final clean filter at the very end of `process_bridge_chat()`, right before returning

### ISSUE 2 — JoJo failing to recall memory

**Symptoms:**
- Questions like "When was I born?" fail to recall stored memory
- Memory context is not being used by external model

**Root Cause:**
- Hybrid chain reasoning overwrites retrieved memory context
- Retrieved memory is not marked as authoritative
- No explicit "memory recall insertion" exists

**Fix:**
- Added Memory Recall Hook in `bridge_service.py` BEFORE generating final hybrid prompt
- Retrieves relevant user memory using `memory_agent.search_memories()`
- Injects clean memory excerpts into system prompt
- External model MUST use that memory to answer clearly

## Changes Applied

### PATCH 1 — Update filter_chain.py

**File:** `src/ai_factory/bridge/filter_chain.py`

Added new `clean_output()` function with specific pattern matching:

```python
def clean_output(text: str) -> str:
    """
    Final clean filter that removes all internal noise from text output.
    This MUST be applied at the very end of the chain, after hybrid enrichment.
    """
    if not text:
        return text
    
    # Remove unified reasoning prefix
    text = re.sub(r"JoJo['']s unified reasoning:\s*", "", text, flags=re.IGNORECASE)
    
    # Remove [Local], [External]
    text = re.sub(r"\[(Local|External)\]", "", text)
    
    # Remove numeric memory brackets like [3641]
    text = re.sub(r"\[\d+\]", "", text)
    
    # Remove any remaining bracketed metadata
    text = re.sub(r"\[[^\]]+\]", "", text)
    
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()
    
    return text
```

### PATCH 2 — Update bridge_service.py (Final Clean)

**File:** `src/ai_factory/bridge/bridge_service.py`

Replaced `filter_output()` with `clean_output()` at the very end, right before returning:

```python
# FINAL CLEAN BEFORE RETURN - MUST be applied after hybrid enrichment
final_text = merged
if isinstance(final_text, str):
    final_text = clean_output(final_text)
else:
    final_text = clean_output(str(final_text))

return {
    "response_text": final_text,
    ...
}
```

### PATCH 3 — Add Memory Recall Hook

**File:** `src/ai_factory/bridge/bridge_service.py`

Added Memory Recall Hook BEFORE generating final hybrid prompt:

```python
# Memory recall hook - retrieve relevant user memory BEFORE generating final hybrid prompt
user_memory = memory_agent.search_memories(user_input or "", limit=5)
clean_memory = []
for m in user_memory or []:
    # Ensure we use only clean summaries
    summary = m.get("summary") or m.get("goal") or ""
    if summary:
        clean_memory.append(summary)
memory_context = "\n".join(clean_memory).strip()

# Build system context with identity and memory recall
system_context = get_identity_prompt()
if memory_context:
    system_context += f"\n\nRelevant user memory:\n{memory_context}\n\nUse this memory to answer clearly."
```

## Execution Order

The correct order of execution is now enforced:

1. **local_reasoning** - Deterministic local summary
2. **memory_retrieval** - Memory Recall Hook retrieves relevant user memory
3. **external_enrichment** - External model receives identity + memory context
4. **reflection / internal rewrite** - Optional empathetic reinforcement
5. **clean_output** ← **MUST BE LAST** - Final clean filter removes all noise
6. **return final message** - Clean, unified response

## Testing Checklist

After applying fixes, test with:

### Test 1: Identity Query
- **User:** "Who are you?"
- **Expected:** Clean single-sentence identity reply (no reasoning tokens)

### Test 2: User Identity Query
- **User:** "Who am I?"
- **Expected:** "You are Nirdesh…" (from memory)

### Test 3: Memory Recall
- **User:** "When was I born?"
- **Expected:** "You were born on July 8, 2001 in Kathmandu." (from stored memory)

### Test 4: General Query
- **User:** "Explain Blender 3D"
- **Expected:** Clean 1-paragraph answer with no noise, no `[Local]`, no `[External]`, no memory chunk IDs

## Files Modified

1. `src/ai_factory/bridge/filter_chain.py` - Added `clean_output()` function
2. `src/ai_factory/bridge/bridge_service.py` - Added Memory Recall Hook + final clean filter
3. `src/ai_factory/version.py` - Updated to v3.9.2
4. `logs/_codex_phase.marker` - Added phase 3.9.2 entry

## Status

✅ **All patches applied idempotently**

The system now:
- Applies final clean filter at the very end (after hybrid enrichment)
- Retrieves and injects relevant user memory into system prompt
- Ensures external model uses memory context to answer clearly
- Returns only clean, unified responses with no internal noise

