# 🚀 AI Factory Builder — Phase 4 Preview (Agent Supervisor MCP)

This document outlines the next major milestone: a Supervisor MCP that coordinates the Planner, Memory, and Debugger to execute multi‑step tasks with feedback loops.

---

## 🧠 Vision

Build a lightweight, local‑first agent orchestration layer that:

- Breaks down goals into actionable steps (via Planner)
- Executes code safely and validates results (via Debugger)
- Logs and recalls context/history (via Memory)
- Iterates until done or blocked, producing a verifiable audit trail

---

## 🧩 Planned Components

- Supervisor Service (`ai_factory/supervisor/`)
  - State machine / loop controller
  - Policies for retries, backoff, and step transitions
  - Trace persistence to Memory MCP (new `supervisor_runs` table)

- Router integration
  - Endpoints: `/supervisor/start`, `/supervisor/status/{id}`, `/supervisor/cancel/{id}`
  - Optional webhook/event stream for UI progress

- Memory integration
  - Read/write supervisor traces alongside planner/debugger records
  - Semantic retrieval of prior runs to guide planning/execution

- Debugger integration
  - Controlled code execution with parameterized timeouts
  - Automatic log ingestion + indexing of outputs

---

## ⚙️ Data Model (Draft)

- `supervisor_runs`
  - `id` (PK)
  - `request_id` (indexed)
  - `created_at` (UTC)
  - `goal` (TEXT)
  - `status` (enum: running/succeeded/failed/canceled)
  - `steps` (JSON) — planned and executed steps
  - `artifacts` (JSON) — paths, outputs, logs

---

## 🔗 Control Flow (Draft)

1. Receive goal → create supervisor run (persist immediately)
2. Call Planner → receive initial plan steps
3. For each step:
   - If code is required → call Debugger, capture outputs
   - Log step results to Memory; index for search
   - Decide next step based on outcome or user policy
4. Terminate with final status and artifacts

---

## 📋 Preparatory Work

- Add combined `/events` view (optional): unified stream of planner + debugger + supervisor entries
- Extend Memory embeddings with lightweight summarization of long outputs
- Graceful cancellation hooks for long‑running debug runs
- Minimal UI: progress view + stream of logs (optional)

---

## ✅ Phase 4 DoD (Definition of Done)

- Supervisor routes shipped and documented
- Persistent records with reproducible traces
- End‑to‑end tests covering a small supervised task
- Local‑first operation with no external model requirements by default

