# Hotfix v3.9.1 - Identity Injection + Filter Chain Enforcement

**Version:** v3.9.1-hotfix-unified-clean  
**Date:** 2025-11-12T17:28:03Z  
**Phase:** 3.9.1

## Overview

This hotfix ensures that JoJo's unified identity is always injected into the hybrid reasoning pipeline and that all output is properly filtered to remove internal debug noise, memory chunks, and prefixes.

## Changes Applied

### 1. Bridge Fix — Always Apply Identity & Emotion Layer

**File:** `src/ai_factory/bridge/bridge_service.py`

- Added imports for `build_identity_system_prompt` and `build_identity_context_for_local`
- Modified `process_bridge_chat()` to:
  - Always apply identity layer at the top of the function
  - Inject identity context into local reasoning with proper prefix
  - Inject identity system prompt into external calls
  - Use `filter_output()` instead of `clean_hybrid_output()` for final cleaning
  - Removed raw memory chunks from prompts (passed empty list to `_compose_prompt`)

**Key Changes:**
```python
# Always apply identity layer at the top
identity_prompt = build_identity_system_prompt()
local_prefix = build_identity_context_for_local()

# Inject identity into local reasoning
local_summary = f"{local_prefix}\nUser: {sanitized}\n{local_summary}"

# Inject identity into external prompt
final_prompt = (
    identity_prompt + "\n\n" +
    f"Tone: {persona_tone}\n\n" +
    get_external_enrichment_context() + "\n\n" +
    _compose_prompt(local_summary, [])  # No raw memory chunks
)

# Use robust filter_output for final cleaning
cleaned_response = filter_output(merged)
```

### 2. Filter Chain Must Run Every Time

**File:** `src/ai_factory/bridge/filter_chain.py`

- Added new `filter_output(text: str) -> str` function with robust pattern matching
- Removes:
  - `[Local]`, `[External]` prefixes (case-insensitive)
  - Memory chunk IDs like `[3597]`, `[123]`
  - "Summarize this: ..." patterns
  - "my openai key is ..." patterns (privacy cleanup)
  - Memory chunk references, RAG scores, advisor noise, model think logs
  - Raw hybrid_output fields, memory query traces, chunk preview markers
  - Collapses repeated whitespace and multiple newlines

**Key Function:**
```python
def filter_output(text: str) -> str:
    """Robust filter function that removes all internal noise from text output."""
    # Comprehensive pattern removal for clean output
    ...
```

### 3. Identity Layer Builders

**File:** `src/ai_factory/identity/jojo_identity.py`

- Added `build_identity_system_prompt()` function
- Added `build_identity_context_for_local()` function
- These functions provide the identity injection points for bridge service

**New Functions:**
```python
def build_identity_system_prompt() -> str:
    """Build the full system prompt for identity injection into external calls."""
    return get_identity_prompt()

def build_identity_context_for_local() -> str:
    """Build the identity context prefix for local reasoning."""
    return get_local_reasoning_prefix()
```

### 4. Hybrid Fix — No Raw Memory in Prompts

**File:** `src/ai_factory/bridge/bridge_service.py`

- Modified `_compose_prompt()` to remove raw memory chunk injection
- Memory is now used only internally by the advisor, not appended to prompts
- Prevents memory chunk IDs and summaries from appearing in user-facing output

**Key Change:**
```python
def _compose_prompt(local_summary: str, ctx_items: List[str]) -> str:
    # No raw memory injection — memory is used only by the advisor internally
    return (
        "You are JoJo's external reasoning partner.\n"
        "Summarized local reasoning follows.\n\n"
        f"Local summary:\n{local_summary}\n\n"
    )
```

### 5. Advisor Verification

**File:** `src/ai_factory/advisor/advisor_service.py`

- Verified that advisor does not return raw memory chunks
- All memory access is through safe selection functions (`select_safe_snippets`)
- Context preview is properly wrapped and sanitized

### 6. Version & Phase Marker Update

**Files:**
- `src/ai_factory/version.py` → Updated to `v3.9.1-hotfix-unified-clean`
- `logs/_codex_phase.marker` → Added phase 3.9.1 entry

## Testing Checklist

- [x] Identity layer always applied in `process_bridge_chat()`
- [x] `filter_output()` function created and integrated
- [x] Raw memory chunks removed from prompts
- [x] No linter errors
- [x] Phase marker updated
- [x] Version bumped to v3.9.1

## Expected Behavior

After this hotfix:
1. **Identity Injection:** Every chat response includes JoJo's unified identity in both local and external reasoning paths
2. **Clean Output:** All responses are filtered through `filter_output()` to remove:
   - `[Local]` and `[External]` prefixes
   - Memory chunk IDs like `[3597]`
   - "Summarize this: ..." patterns
   - "my openai key is ..." patterns
   - All other internal debug noise
3. **No Raw Memory:** Memory chunks are never appended to prompts or shown in responses
4. **Unified Identity:** JoJo speaks with one consistent voice, no persona switching

## Files Modified

1. `src/ai_factory/bridge/bridge_service.py` - Identity injection + filter_output integration
2. `src/ai_factory/bridge/filter_chain.py` - Added robust `filter_output()` function
3. `src/ai_factory/identity/jojo_identity.py` - Added identity builder functions
4. `src/ai_factory/version.py` - Version bump to v3.9.1
5. `logs/_codex_phase.marker` - Phase marker entry

## Status

✅ **All hotfix tasks completed idempotently**

The system now enforces:
- Identity injection at the top of every hybrid reasoning chain
- Robust filtering of all output through `filter_output()`
- No raw memory chunks in prompts or responses
- Unified JoJo identity in every interaction

