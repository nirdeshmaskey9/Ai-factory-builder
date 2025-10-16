# 🧠 AI Factory Builder — v3.0 Architecture

This document describes the current system at the v3.0 Golden Build. The platform is a local‑first FastAPI application that exposes three cooperating MCPs (Model/Memory/Control Plane components):

- Router Core (Phase 1)
- Memory MCP (Phase 2)
- Debugger MCP (Phase 3)

The system is designed to be modular, offline‑friendly, and testable end‑to‑end.

---

## 🧩 High‑Level Overview

- App server: FastAPI + Uvicorn
- Configuration: Pydantic Settings (env‑driven), local `.env`
- Logging: Console + rotating file (under `ai_factory/data/logs/app.log`)
- Storage:
  - SQLite (append‑only event stores) under `ai_factory/data/memory.db`
  - Chroma vector store (stubbed, persistent folder) under `ai_factory/data/chroma`
- Tests: `pytest` covering health, planner, memory, and debugger flows

---

## ⚙️ Services and Data Flow

1) Router Core
- Entrypoint: `ai_factory/main.py`
- Routers:
  - `GET /healthcheck` — liveness probe
  - `POST /planner/dispatch` — accepts `{prompt, task_type}` and returns a structured plan
- Planner: `ai_factory/services/planner_service.py`
  - Stub heuristic planner that decomposes the prompt into steps

2) Memory MCP
- DB models: `MemoryEvent` (and `DebuggerRun`) in `ai_factory/memory/memory_db.py`
- APIs (router): `ai_factory/memory/routers/memory_router.py`
  - `GET /memory/logs?limit=N` — latest planner events
  - `GET /memory/search?q=...&n=M` — semantic search via Chroma stub
  - `GET /memory/snapshot?limit=K` — write JSONL snapshot under `ai_factory/data/snapshots/`
- Vector memory: `ai_factory/memory/memory_embeddings.py`
  - Uses a persistent Chroma client
  - Falls back to an in‑repo stub and FAKE hash embeddings if model downloads are not available
- Middleware: `ai_factory/services/middleware.py`
  - `MemoryLoggerMiddleware` automatically logs `POST /planner/dispatch` requests + responses into SQLite and indexes them into Chroma

3) Debugger MCP
- Runner: `ai_factory/debugger/debugger_runner.py`
  - Executes Python snippets via `subprocess.run` with a 5s timeout
  - Captures `stdout`, `stderr`, and `exit_code`
- Store: `ai_factory/debugger/debugger_store.py`
  - Persists run metadata into SQLite table `debugger_runs`
- APIs (router): `ai_factory/debugger/routers/debugger_router.py`
  - `POST /debugger/run` — run code and persist results
  - `GET /debugger/logs?limit=N` — latest runs
  - `GET /debugger/search?q=...&n=M` — text search across code/outputs
- Optional middleware: `DebugLoggerMiddleware` (timing headers for `/debugger/*`)

---

## 🗄️ Storage Layout

- SQLite file: `ai_factory/data/memory.db`
  - Tables:
    - `memory_events` — planner dispatch request/response records
    - `debugger_runs` — code execution results
- Vector store directory: `ai_factory/data/chroma/`
- Log directory: `ai_factory/data/logs/` (rotating file `app.log`)
- Snapshots: `ai_factory/data/snapshots/` (JSONL)

---

## 📁 Repository Structure (key paths)

```
ai_factory/
  main.py                      # FastAPI app (lifespan, routers, middleware)
  config.py                    # Settings (env‑driven)
  logging_setup.py             # Console + rotating file
  routers/
    health.py                  # GET /healthcheck
    planner.py                 # POST /planner/dispatch
  services/
    planner_service.py         # Stub planner
    middleware.py              # Memory/Debug logger middleware
  memory/
    memory_db.py               # SQLite engine + ORM models + init_db()
    memory_store.py            # Append‑only writes and reads
    memory_embeddings.py       # Chroma stub + FAKE embeddings fallback
    routers/memory_router.py   # /memory/logs, /memory/search, /snapshot
  debugger/
    debugger_runner.py         # Safe subprocess code runner (Python)
    debugger_store.py          # Persist/retrieve/search runs
    routers/debugger_router.py # /debugger/run, /logs, /search
  data/
    logs/                      # app.log
    chroma/                    # vector store persistence (stub or real)
    memory.db                  # SQLite database
```

---

## 🔌 Runtime Integration

- Lifespan startup (`main.py`):
  - Ensure log directory, configure logging
  - Initialize the SQLite schema (`init_db()`)
  - Log startup banner for Phase 3
- Middleware:
  - `MemoryLoggerMiddleware` adds `X-Request-ID` and `X-Duration` and logs/embeds planner events
- Routers:
  - Health, Planner, Memory, Debugger all mounted on the FastAPI app

---

## 🚀 Usage

- Start: `uvicorn ai_factory.main:app --reload`
- Planner (auto‑logged):
  ```bash
  curl -s -X POST http://127.0.0.1:8000/planner/dispatch \
    -H "Content-Type: application/json" \
    -d '{"prompt":"Create a repo; add CI; write tests","task_type":"coding"}'
  ```
- Debugger:
  ```bash
  curl -s -X POST http://127.0.0.1:8000/debugger/run \
    -H "Content-Type: application/json" \
    -d '{"code":"print(2+2)","language":"python"}'
  ```
- Memory APIs:
  ```bash
  curl -s "http://127.0.0.1:8000/memory/logs?limit=5"
  curl -s "http://127.0.0.1:8000/memory/search?q=tests&n=3"
  curl -s "http://127.0.0.1:8000/memory/snapshot?limit=50"
  ```

---

## 🔒 Local‑First Principles

- No external model calls are required by default
- Vector store gracefully falls back to a bundled Chroma stub and FAKE embeddings
- All data is stored under `ai_factory/data/` and covered by `.gitignore` for runtime artifacts

---

## ✅ Test Coverage

- `tests/test_health.py` — health check
- `tests/test_planner.py` — planner dispatch behavior
- `tests/test_memory_log.py`, `tests/test_memory_search.py` — event logging and search
- `tests/test_debugger_run.py`, `tests/test_debugger_search.py` — code execution and search

---

## 📌 Version

- v3.0 Golden Build (Router Core + Memory MCP + Debugger MCP)
- App title/version (runtime):
  - Title: "AI Factory Builder - Router Core + Memory + Debugger"
  - Version: 0.3.0

