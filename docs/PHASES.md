# 🧩 AI Factory Builder — Phases 1–4 Summary (v4.0)

This document summarizes the delivered phases through the v4.0 release.

---

## 1️⃣ Phase 1 — Router Core

- Goal: Establish a clean FastAPI skeleton with a stub planner.
- Features:
  - `GET /healthcheck` — liveness probe
  - `POST /planner/dispatch` — accepts `{prompt, task_type}` and returns a deterministic plan
  - Logging to console + rotating file
  - Pydantic Settings with `.env` support
- Tech:
  - FastAPI, Uvicorn, Pydantic v2
- Tests:
  - Health and planner request/response

---

## 2️⃣ Phase 2 — Memory MCP

- Goal: Add a local memory layer with semantic recall and automatic logging.
- Features:
  - SQLite event log table `memory_events`
  - Chroma vector store (with in‑repo stub + FAKE embeddings fallback)
  - Middleware that logs every `/planner/dispatch` request + response and indexes for recall
  - Endpoints:
    - `GET /memory/logs?limit=N`
    - `GET /memory/search?q=...&n=M`
    - `GET /memory/snapshot?limit=K` → JSONL under `ai_factory/data/snapshots/`
- Tech:
  - SQLAlchemy, SQLite, (stubbed) Chroma
- Tests:
  - Ensure events are logged via middleware; verify semantic search is callable

---

## 3️⃣ Phase 3 — Debugger MCP

- Goal: Safely execute code, capture outputs, and store results for semantic recall.
- Features:
  - Subprocess runner for Python snippets (`5s` timeout)
  - DB table `debugger_runs` persists request_id, language, code, stdout, stderr, status
  - Endpoints:
    - `POST /debugger/run`
    - `GET /debugger/logs?limit=N`
    - `GET /debugger/search?q=...&n=M`
  - Optional timing middleware for `/debugger/*`
  - Results indexed into the vector store for search
- Tech:
  - Python `subprocess`, SQLAlchemy, (stubbed) Chroma
- Tests:
  - Verify a successful run is persisted and searchable

---

## 4️⃣ Phase 4 — Agent Supervisor MCP

- Goal: Orchestrate Planner → Memory → Debugger into a self‑contained loop.
- Features:
  - Supervisor loop: generate plan, search memory, execute code‑like steps, aggregate results
  - DB table `supervisor_sessions` persists goal, plan (JSON), context, result, status
  - Endpoints:
    - `POST /supervisor/run`
    - `GET /supervisor/status?limit=N`
    - `GET /supervisor/history?limit=N`
- Tech:
  - In‑proc Planner + Memory + Debugger integration with SQLAlchemy persistence
- Tests:
  - Ensure a run returns full payload and is persisted; status/history list sessions; smoke old routes

---

## 5️⃣ Phase 3.9.x — Unified JoJo Identity & Memory Persistence

### Phase 3.9.0 — Unified JoJo Identity (2025-11-12)
- **Goal**: Unify JoJo into single identity, remove all persona modes
- **Features**:
  - Created unified identity layer (`identity/jojo_identity.py`)
  - Created filter chain for clean output (`bridge/filter_chain.py`)
  - Removed all persona mode buttons and multi-persona code
  - Enforced port 8000 for all services
  - Updated UI header to unified identity
- **Result**: Single unified identity, no mode switching

### Phase 3.9.1 — Identity Injection Hotfix (2025-11-12)
- **Goal**: Ensure identity always injected, improve filter chain
- **Features**:
  - Added `filter_output()` function with robust pattern matching
  - Enforced identity injection in bridge service
  - Added identity builder functions
  - Removed raw memory chunks from prompts
- **Result**: Identity always applied, cleaner output

### Phase 3.9.2 — Memory Recall Fix (2025-11-12)
- **Goal**: Fix memory recall reliability
- **Features**:
  - Added `clean_output()` function for final filtering
  - Added memory recall hook in bridge service
  - Enhanced memory context injection into system prompt
- **Result**: Memory recall works, clean final output

### Phase 3.9.3 — Bridge Purification (2025-11-12)
- **Goal**: Fix transcript spam, ensure proper pipeline ordering
- **Features**:
  - Fixed pipeline ordering (memory retrieval FIRST)
  - External model now OVERRIDES local (not merged)
  - Enhanced `clean_output()` removes "User:" transcript spam
  - Added sentence deduplication in filter chain
- **Result**: Clean output, no transcript echoes, proper memory-first flow

### Phase 3.9.4 — Memory Persistence (2025-11-12)
- **Goal**: Ensure memory persists across restarts
- **Features**:
  - Created identity memory seeder (`identity_seeder.py`)
  - Added startup identity memory seeding (idempotent)
  - Created memory diagnostics script
  - Added debug endpoints (`/debug/memory/list`, `/debug/memory/search`)
  - Created memory persistence tests
- **Result**: Memory persists across restarts, identity recall works reliably

### Phase 3.9.4.1 — Stable Release (2025-11-12)
- **Goal**: Fix import errors, improve seeding, add database ping
- **Features**:
  - Fixed `and_` import error (now imports from sqlalchemy)
  - Added database ping function using `text()` to avoid warnings
  - Improved identity seeding with single commit
  - Enhanced debug endpoints format
- **Result**: App starts cleanly, no warnings, identity memories seed reliably

---

## ✅ Current Status — v3.9.4.1

- **Unified JoJo Identity**: Single, consistent AI persona
- **Persistent Memory**: Identity memories seeded on startup, persist across restarts
- **Hybrid Reasoning**: Local trio + optional external enrichment
- **Clean Output**: No debug noise, no `[Local]`/`[External]` prefixes
- **Memory-First Pipeline**: Memory retrieved FIRST before any model runs
- **Port 8000 Enforced**: All services run on consistent port
- **Local Trio Stable**: Strategist, Memory, Executor models optimized for 8GB VRAM

---

## 🚀 How To Run

```bash
python scripts/run_factory.py
```

The application runs on **http://127.0.0.1:8000** (port 8000 enforced).

### Chat Interface
Visit: `http://127.0.0.1:8000/chat`

### Memory Viewer
Visit: `http://127.0.0.1:8000/ui/memory`

### Debug Endpoints
```bash
curl "http://127.0.0.1:8000/debug/memory/list?limit=10"
curl "http://127.0.0.1:8000/debug/memory/search?q=birth"
```

### Setup Ollama Models
```bash
# Windows
.\scripts\setup_ollama.ps1

# Linux/Mac
./scripts/setup_ollama.sh
```

---

## 🧭 What's Next

- **Phase 4.0**: Emotional Engine & Identity Layer Expansion
  - Enhanced emotional awareness
  - Deeper identity integration
  - Advanced memory-powered features
  - Emotional state tracking and response
