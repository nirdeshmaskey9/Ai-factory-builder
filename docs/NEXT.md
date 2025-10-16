# 🚀 AI Factory Builder — Phase 5 Preview (Evaluator MCP)

This document outlines Phase 5: an Evaluator MCP that scores and critiques outputs (plans, code results, and sessions), enabling quality gates and automatic improvement cycles.

---

## 🧠 Vision

Provide an offline‑friendly evaluation layer that:

- Scores plan quality and execution outcomes against criteria
- Detects regressions across sessions
- Suggests improvements and feeds them back to Supervisor/Planner
- Persists evaluations for auditing and trend analysis

---

## 🧩 Planned Components

- Evaluator Service (`ai_factory/evaluator/`)
  - Criteria definition and scoring functions (rule‑based + heuristics, local‑first)
  - Optional model hooks (kept off by default)

- Router integration
  - Endpoints: `/evaluator/evaluate`, `/evaluator/criteria`, `/evaluator/history`

- Memory integration
  - Store `evaluator_runs` with references to supervisor/planner/debugger artifacts
  - Semantic search for similar evaluations and outcomes

---

## 🗄️ Data Model (Draft)

- `evaluator_runs`
  - `id` (PK)
  - `request_id` (indexed)
  - `timestamp` (UTC)
  - `subject_type` (enum: plan|debugger|supervisor)
  - `subject_ref` (foreign key or pointer)
  - `criteria` (JSON)
  - `score` (number)
  - `feedback` (TEXT)

---

## 🔗 Control Flow (Draft)

1. Receive subject and criteria → compute score + feedback
2. Persist evaluation and index feedback into vector memory
3. Optionally notify Supervisor to iterate if quality gates fail

---

## 📋 Preparatory Work

- Define default criteria bundles (readability, test coverage hints, failure rate)
- Add cross‑references from `supervisor_sessions` to evaluations
- Extend docs with evaluation dashboards/queries

---

## ✅ Phase 5 DoD (Definition of Done)

- Evaluator endpoints shipped and documented
- Persistent evaluation records with criteria + score + feedback
- Integration path to Supervisor for corrective loops
- Tests covering scoring, persistence, and retrieval
