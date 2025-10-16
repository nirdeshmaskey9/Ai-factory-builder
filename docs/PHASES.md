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

## ✅ Current Status — v4.0

- Router Core, Memory MCP, Debugger MCP, and Supervisor MCP are stable and tested.
- All storage and logs are local‑first under `ai_factory/data/`.
- The application starts cleanly and serves all routes.

---

## 🚀 How To Run

```bash
uvicorn ai_factory.main:app --reload
```

- Planner:
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

- Memory:
```bash
curl -s "http://127.0.0.1:8000/memory/logs?limit=5"
curl -s "http://127.0.0.1:8000/memory/search?q=tests&n=3"
curl -s "http://127.0.0.1:8000/memory/snapshot?limit=50"
```

---

## 🧭 What’s Next

- Phase 4 — Agent Supervisor MCP
  - Orchestrate Planner + Memory + Debugger to accomplish multi‑step goals
  - Manage task decomposition, execution, and iterative refinement
  - Persist agent traces to Memory MCP for auditable workflows
  - Plan upgrades for model integration while preserving local‑first defaults
