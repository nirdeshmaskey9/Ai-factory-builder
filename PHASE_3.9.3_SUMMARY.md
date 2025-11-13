# Phase 3.9.3 - Bridge Purification + Memory Injection + Output Override

**Version:** v3.9.3-bridge-fix  
**Date:** 2025-11-12T17:49:20Z  
**Phase:** 3.9.3

## Overview

This phase fixes critical issues with transcript spam, memory recall reliability, and pipeline ordering. The hybrid chain now correctly:
- Retrieves memory FIRST before any model runs
- Uses local reasoning as rough draft only
- Uses external model as final authoritative override (not merged)
- Applies clean_output() as the LAST step

## Issues Fixed

### ISSUE 1 — Repeating "User: ..." transcript spam

**Symptoms:**
- "User: who are you? who are you?" repeated in output
- Transcript echoes appearing in responses
- Old conversation history leaking into new responses

**Root Cause:**
- Local summary included "User: {sanitized}" prefix
- Merge function combined local and external with [Local]/[External] tags
- These tags and prefixes were not being fully cleaned

**Fix:**
- Removed "User:" prefix from local summary construction
- External model now OVERRIDES local (not merged)
- Enhanced clean_output() to aggressively remove "User:" patterns

### ISSUE 2 — Memory recall not working reliably

**Symptoms:**
- "When was I born?" fails to recall stored memory
- "Who am I?" doesn't use memory context
- "Which country am I from?" doesn't recall

**Root Cause:**
- Memory was retrieved but not injected into system prompt FIRST
- Memory context was added after local reasoning, not before
- External model wasn't explicitly instructed to use memory

**Fix:**
- Memory retrieval moved to FIRST step (before any model runs)
- Memory context injected into system prompt FIRST
- External model explicitly instructed to use memory context

### ISSUE 3 — Pipeline ordering incorrect

**Symptoms:**
- Local and external outputs merged with [Local]/[External] tags
- Clean output applied too early
- Memory injected too late in the chain

**Root Cause:**
- Pipeline order was: local → memory → external → merge → clean
- Should be: memory → system prompt → local (draft) → external (final) → clean

**Fix:**
- Reordered pipeline to: memory FIRST → system prompt → local draft → external override → clean LAST
- External output is now the final answer (not merged with local)

## Changes Applied

### PATCH 1 — Update filter_chain.py (Brutal Final Clean)

**File:** `src/ai_factory/bridge/filter_chain.py`

Enhanced `clean_output()` function with aggressive pattern removal:

```python
def clean_output(text: str) -> str:
    """
    Final clean filter that removes all internal noise from text output.
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
```

**Key Improvements:**
- Removes "User: ..." transcript echoes completely
- Deduplicates sentences to prevent repetition
- More aggressive bracket removal
- Collapses extra whitespace

### PATCH 2 — Fix bridge_service.py Pipeline Ordering

**File:** `src/ai_factory/bridge/bridge_service.py`

Completely restructured `process_bridge_chat()` function:

**New Pipeline Order:**
1. **Memory retrieval FIRST** - Before any model runs
2. Build system prompt with identity + memory
3. Local reasoning → rough draft only (NO "User:" prefix)
4. External model → final authoritative rewrite (OVERRIDES local)
5. clean_output() applied LAST

**Key Changes:**
- Memory retrieved FIRST before any model runs
- System prompt built with identity + memory injected FIRST
- Local summary is just a rough draft (no "User:" prefix)
- External model provides final answer (not merged with local)
- Removed `_merge_local_external()` call
- External output is the final answer directly

**Before:**
```python
local_summary = f"{local_prefix}\nUser: {sanitized}\n{local_summary}"
# ... memory retrieved later ...
merged = _merge_local_external(local_summary, ext_out)
```

**After:**
```python
# Memory retrieved FIRST
user_memory = memory_agent.search_memories(user_input or "", limit=5)
# ... build system prompt with memory ...
# Local draft only (no "User:" prefix)
local_draft = local_summary
# External OVERRIDES local (not merged)
final_answer = ext_out
```

### PATCH 3 — Update Version

**File:** `src/ai_factory/version.py`

Updated to `v3.9.3-bridge-fix`

## Execution Order (Enforced)

The correct order is now:

1. **memory_retrieval** ← FIRST, before any model runs
2. **system_prompt** ← Built with identity + memory injected
3. **local_reasoning** → Rough draft only (no "User:" prefix)
4. **external_enrichment** → Final authoritative answer (OVERRIDES local)
5. **clean_output** ← MUST BE LAST
6. **return final message** → Clean, unified response

## Testing Checklist

After applying fixes, test with:

### Test 1: Identity Query
- **User:** "Who are you?"
- **Expected:** "I am JoJo, your unified personal AI companion." (clean, no transcript spam)

### Test 2: User Identity Query
- **User:** "Who am I?"
- **Expected:** "You are Nirdesh Maskey." (from memory)

### Test 3: Memory Recall - Birthdate
- **User:** "When was I born?"
- **Expected:** "You were born July 8, 2001, in Kathmandu, Nepal." (from memory)

### Test 4: Memory Recall - Country
- **User:** "Which country am I from?"
- **Expected:** "You're from Nepal." (from memory)

### Test 5: General Query
- **User:** "Explain Blender 3D."
- **Expected:** Clean technical explanation, not mixed with old transcripts, no "User:" spam

## Files Modified

1. `src/ai_factory/bridge/filter_chain.py` - Enhanced `clean_output()` with brutal cleaning
2. `src/ai_factory/bridge/bridge_service.py` - Fixed pipeline ordering, external override
3. `src/ai_factory/version.py` - Updated to v3.9.3
4. `logs/_codex_phase.marker` - Added phase 3.9.3 entry

## Status

✅ **All patches applied idempotently**

The system now:
- Retrieves memory FIRST before any model runs
- Injects memory into system prompt FIRST
- Uses local reasoning as rough draft only (no "User:" prefix)
- Uses external model as final authoritative override (not merged)
- Applies clean_output() as the LAST step
- Removes all transcript spam, duplicates, and internal noise

## Expected Behavior After Fix

**No more:**
- "User: who are you? who are you?" repeated spam
- Repeated FastAPI memories
- Hidden local/external merge artifacts
- Failure to recall birthdate
- Failure to recall country
- Transcript echo spam

**JoJo will:**
- Respond precisely, warmly, cleanly
- Recall memory reliably (birthdate, country, identity)
- Provide clean answers without transcript spam
- Use external model as final authoritative answer

