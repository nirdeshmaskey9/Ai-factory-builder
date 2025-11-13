# Changelog

## v3.9.4.1-nl (2025-11-12) - Stable Release
- **Fixed**: Import error for `and_` (now imports from sqlalchemy)
- **Added**: Database ping function using `text()` to avoid SQLAlchemy warnings
- **Improved**: Identity seeding with single commit (more efficient)
- **Enhanced**: Debug endpoints return `{id, key, value, tags}` format
- **Updated**: Startup sequence with database ping verification
- **Result**: App starts cleanly, no warnings, identity memories seed reliably

## v3.9.4-memory-persistence (2025-11-12)
- **Added**: Identity memory seeder (`identity_seeder.py`)
- **Added**: Startup identity memory seeding (idempotent)
- **Added**: Memory diagnostics script (`scripts/memory_diagnostics.py`)
- **Added**: Debug endpoints (`/debug/memory/list`, `/debug/memory/search`)
- **Added**: Memory persistence tests (`tests/test_memory_persistence.py`)
- **Result**: Memory persists across restarts, identity recall works reliably

## v3.9.3-bridge-fix (2025-11-12)
- **Fixed**: Pipeline ordering (memory retrieval FIRST)
- **Fixed**: External model now OVERRIDES local (not merged)
- **Enhanced**: `clean_output()` removes "User:" transcript spam
- **Added**: Sentence deduplication in filter chain
- **Result**: Clean output, no transcript echoes, proper memory-first flow

## v3.9.2-unified-clean-final (2025-11-12)
- **Added**: `clean_output()` function for final filtering
- **Added**: Memory recall hook in bridge service
- **Enhanced**: Memory context injection into system prompt
- **Result**: Memory recall works, clean final output

## v3.9.1-hotfix-unified-clean (2025-11-12)
- **Added**: `filter_output()` function with robust pattern matching
- **Enforced**: Identity injection in bridge service
- **Added**: Identity builder functions
- **Removed**: Raw memory chunks from prompts
- **Result**: Identity always applied, cleaner output

## v3.9.0-unified-jojo (2025-11-12)
- **Created**: Unified JoJo identity layer (`identity/jojo_identity.py`)
- **Created**: Filter chain for clean output (`bridge/filter_chain.py`)
- **Removed**: All persona mode buttons and multi-persona code
- **Enforced**: Port 8000 for all services
- **Updated**: UI header to "JoJo Planet v3.9.0 — Unified Identity · Hybrid Brain"
- **Result**: Single unified identity, no mode switching

## v3.7.0-hybrid-brain-initialization (2025-11-12)
- **Optimized**: Local Trio models for 8GB VRAM:
  - Strategist: Qwen 2 1.5B Instruct Q4
  - Memory: Mistral 7B Instruct v0.3 Q4
  - Executor: Phi-3 Mini 3.8B Q4
- **Created**: Ollama setup scripts (PowerShell and Bash)
- **Created**: Trio validation script
- **Result**: Optimized local AI models, hybrid reasoning established

## v1.2-master-stable
- Core hardening: atomic manifest writes, template fallbacks, evaluator summary fallback.
- Memory MCP: evaluation results persisted to SQLite with retries + diagnostics.
- Health: /factory/info extended with timestamp and MCP summary.
- Startup/shutdown logs and global exception logging middleware.
- Planner: domain blueprint helper + regression tests.
- Scripts: Factory diagnostics (to be run manually) added.

## v1.2-master
- Add domain detector and modular builders for `web`, `cli`, `ml`.
- Add `POST /factory/create` route and ADR logging.
- Add evaluator suites per domain and a runner.
- Preserve watchdog, PID tracking, env validator, and orchestrator.
