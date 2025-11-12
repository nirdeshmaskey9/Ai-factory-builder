# AI Factory Builder — Canonical Reference (JoJo/Qwen Alignment)

This document is the canonical, lossless reference for the AI Factory Builder codebase and its operational AI persona, JoJo. It reconciles the exact behavior of the code (as of the current repository state) with authoritative clarification about identity boundaries, architectural intent, and near‑term evolution. Treat this as the single comprehensive source to onboard humans and AIs to the project.

Contents
- 1) Executive Overview (Plain + Technical)
- 2) Project Evolution Timeline (Milestones & Shifts)
- 3) System Map (Human + Technical)
- 4) Architecture & Components (Tabular + Detailed)
- 5) JoJo (Qwen) vs AI Factory — Roles & Integration
- 6) Native AIs (Local Trio) — Definitions & Contracts
- 7) Teacher Models (Cloud Specialists) — Usage & Capture
- 8) Memory & RAG — Data Model & Operations
- 9) Runtime Behavior (Startup → /chat → Logging)
- 10) UI / Operator Controls & Telemetry
- 11) Version/Phase State — Reality vs Target
- 12) Current Status (Checkpoint v4.9)
- 13) Roadmap (Near → Mid)
- 14) Operational Playbooks (How‑To)
- 15) Security, Privacy, and Cost
- 16) Testing & Quality
- 17) Essence Summary (3 sentences)

---

## 1) Executive Overview (Plain + Technical)

Plain language
- AI Factory Builder is JoJo’s city and toolset. It plans, builds, evaluates, deploys, and remembers. JoJo—the sovereign AI persona—speaks through the Bridge, decides routes via the Advisor, and uses the Factory’s memory and services to help humans.
- Today, JoJo is embodied as a local Qwen 7B model (with planned LoRA adapters for Identity, Truth, Tools, Strategy). The Factory provides her environment: durable memory (SQLite), semantic recall (FAISS + SentenceTransformers), safe redaction, UI control, and orchestrated workflows.

Technical summary
- Backend: FastAPI app (`ai_factory/main.py`) mounting modular routers (Planner, Builder, Evaluator, Orchestrator, Advisor, Bridge, Memory, RAG, UI, Deployer, Router V2, System Health, WebSockets). Global exception middleware logs and returns JSON 500s with error IDs.
- Persistence: SQLite via SQLAlchemy models (`ai_factory/memory/memory_db.py`) for memory entries, embeddings, dialogue turns/summaries, mood log, model usage, evaluation results. Semantic layer: FAISS + SentenceTransformers (`ai_factory/rag/*`).
- Reasoning flows: Bridge redacts and synthesizes local responses, optionally enriches with external teachers (OpenAI/Anthropic/Gemini), merges results, and writes to the learning ledger. Advisor decides local trio vs cloud based on health/privacy.
- UI: Jinja2 templates + static JS/CSS (`ai_factory/ui/*`), control panel toggles (`/ui/toggle_mock`, `/ui/toggle_rag`, `/ui/control_state`), dashboards, and WebSocket telemetry (`/ws/runs`, `/ws/logs/{run_id}`, `/ws/chat`).
- Native “Local Trio”: strategist/memory/executor roles managed under a unified Ollama daemon; health monitored by a background trio manager thread.

---

## 2) Project Evolution Timeline (Milestones & Shifts)

Identity shift
- Historically: “JoJo” referred to the entire Factory. Now: JoJo is a sovereign persona (Qwen 7B) operating within the Factory—her body, city, and nervous system.

Notable phases (from `logs/_codex_phase.marker` and commits)
- 3.3.x Hybrid Bridge: Emergence of hybrid chat—local deterministic summary + external enrichment with redaction.
- 3.4.0 UI Awakening: Dashboarding and control panel bring visibility and toggles.
- 3.5.x Rational Core: Align runtime flags, memory logging, advisor decision traceability; reinforce deterministic fallbacks (reported in `ai_factory/version.py` as 3.5.2 “rational-core”).
- 3.9 Local Trio v4 Swap: Centralized local trio registry; advisor and routers adjusted to unified host probing.
- 4.0 RAG + Memory Feedback Integration: FAISS + SentenceTransformers retrieval, Memory MCP feedback weighting; on‑demand sync; logs show “rag-perfection”.
- 4.9 Structural Rebirth & Clean Rebase: Cleanup of legacy UI assets, enhanced system status, consolidation passes.

Why each shift
- From monolithic “JoJo = System” to “JoJo = mind”: clarifies boundaries enabling LoRA distillation and multi‑persona evolution.
- Bridge/Advisor: privacy‑first hybrid thinking; local always works, cloud optional, everything observable.
- RAG Perfection: boost semantic recall with human feedback weighting; measurable retrieval quality.
- Structural Rebirth: reduce entropy; clarify control surfaces; prepare for background sync/event‑driven telemetry.

---

## 3) System Map (Human + Technical)

Human map (org chart metaphor)
- Advisor (brainstem): route decisions—local vs cloud, role selection.
- Bridge (voice & conversation cortex): redaction, local synthesis, teacher enrichment, merging, mood logging.
- Memory (hippocampus): SQLite learning ledger + FAISS semantic layer with feedback weighting.
- Orchestrator (prefrontal workflow): plan→build→evaluate→deploy, retries/repairs, run history.
- Planner/Builder/Evaluator (departments): plan tasks, construct artifacts, and score results.
- UI (eyes & dashboard): control panel, live telemetry, chat.
- Deployer (ops): preview processes watchdog, artifact publishing.
- Router V2 (switchboard): model registry and selection for non‑chat operations.
- Supervisor/System Health (immune system): cross‑cutting logging, health snapshots, audits.

Technical map (key modules)
- Planner: `ai_factory/planner/planner_agent.py`; router `ai_factory/routers/planner.py`.
- Builder: `ai_factory/builder/*`, templates under `ai_factory/templates/*`, base `ai_factory/builders/base.py`.
- Evaluator: `ai_factory/evaluator/*` with suites in `evaluator/suites/*`.
- Orchestrator: `ai_factory/orchestrator/*` (agent/store/router), services in `ai_factory/services/*`.
- Advisor: `ai_factory/advisor/advisor_service.py` + router + `advisor/trio_manager.py`.
- Bridge: `ai_factory/bridge/bridge_service.py`, `ai_factory/bridge/chatgpt_proxy.py`.
- Memory: `ai_factory/memory/memory_agent.py`, schema `ai_factory/memory/memory_db.py`, router `ai_factory/memory/routers/memory_router.py`.
- RAG: `ai_factory/rag/*` (service, vector_db, doc_loader, router).
- MCP: `ai_factory/memory/memory_mcp.py` (feedback/summary files and integration).
- UI: `ai_factory/ui/*` (routers/templates/static) with websockets in `ui/ws_router.py` and `ui/chat_router.py`.
- Router V2: `ai_factory/router_v2/*` and service `ai_factory/services/router_v2_service.py`.
- Deployer: `ai_factory/deployer/*` and watchdog `ai_factory/services/watchdog_service.py`.
- System: health/report `ai_factory/system/*`; global config and runtime flags in `ai_factory/config.py`, `ai_factory/config_runtime_flags.py`.

Request flows
- User → `/ws/chat` → Bridge redaction + local summary → persona/tone → Advisor decision/teacher (optional) → merge → Memory (dialogue/mood/auto‑learn) → UI stream.
- Goal → Orchestrator `/orchestrator/run` → Plan → Route (Router V2/Advisor) → Build → Evaluate (score) → Deploy (opt) → Memory/logs → UI history and WS feeds.

Background tasks
- Trio Manager (thread) probes Ollama health per role.
- Deployer Watchdog (async task) restarts crashed previews.

---

## 4) Architecture & Components (Tabular + Detailed)

| Component | Purpose | Key Files/Functions |
|---|---|---|
| Planner | Convert prompt → plan, domain | `planner/planner_agent.py:plan_task`, `routers/planner.py` |
| Builder | Generate artifacts/templates | `builder/builder_agent.py`, `builders/*/builder.py`, `builders/base.py` |
| Evaluator | Score artifacts (web/cli/ml) | `evaluator/evaluator_agent.py`, `evaluator/suites/*`, `evaluator/evaluator_router.py` |
| Orchestrator | Plan→build→evaluate→deploy runs, retries | `orchestrator/orchestrator_agent.py`, `orchestrator_router.py`, `orchestrator_store.py` |
| Advisor | Choose local trio vs cloud; health | `advisor/advisor_service.py`, `advisor_router.py`, `advisor/trio_manager.py` |
| Bridge | Hybrid chat: redact, local synth, teacher enrich | `bridge/bridge_service.py`, `bridge/chatgpt_proxy.py` |
| Memory | Durable ledger; search/rank/recall | `memory/memory_agent.py`, `memory_db.py`, `memory/routers/memory_router.py` |
| RAG | FAISS + embeddings; feedback-weighted retrieval | `rag/rag_service.py`, `rag/vector_db.py`, `rag/doc_loader.py` |
| MCP | File-based feedback/summaries integration | `memory/memory_mcp.py` |
| UI | Operator dashboards; control panel; chat | `ui/*` routers, templates, static |
| WebSockets | Live runs/logs/chat | `ui/ws_router.py`, `ui/chat_router.py` |
| Router V2 | Model registry/selection, provider calls | `router_v2/*`, `services/router_v2_service.py` |
| Supervisor | Oversight, logging | `supervisor/*`, `services/middleware.py` |
| Deployer | Preview mgmt + watchdog | `deployer/*`, `services/watchdog_service.py` |
| System | Health/report | `system/*` |
| Config | Settings/env + runtime flags | `config.py`, `config_runtime_flags.py` |

Detailed behavior highlights
- Planner: Detects domain deterministically; uses OpenAI when configured; returns structured steps. Errors degrade to deterministic stub.
- Builder: Writes build inputs/manifest atomically, logs build warnings, delegates to domain builders; `build_domain` is abstract and overridden by domain implementations.
- Evaluator: Suite‑specific tests; persists `EvaluationResult` in DB; routes expose scores/history.
- Orchestrator: Persists run metadata, writes `logs/orchestrator/plan_*.json` and `run_*.json`, consults Advisor, optionally includes RAG context; repair/retry logic is policy‑driven via `services/orchestrator_service.py`.
- Advisor: `verify_local_health` pings Ollama `/api/version` + `/api/generate` with short client timeouts and exponential backoff; `route_task` optionally fetches RAG context and logs decisions to memory. Router offers `/advisor/models`, `/advisor/trio_health` with manager integration.
- Bridge: `_redact_private` masks secrets/paths/emails; `_local_reason` yields deterministic summary with empathy; `call_gpt5` delegates to OpenAI via `chatgpt_proxy` unless mock; merges outputs; persists dialogue turns and mood; auto‑learn and auto‑reflection memories.
- Memory: Store/search/rank with (semantic, tag, recency) weights; `ensure_embedding` persists JSON‑encoded vectors; `model_usage` table logs provider usage.
- RAG: Build/load FAISS index; ingestion supports plain/PDF via “unstructured” pipeline; retrieval re‑weights with MCP feedback; sync from `memory_mcp.get_recent_memories()` and writes `data/vector_db/last_sync.txt`.
- UI/WS: `/ui/system_status` exposes version, milestone, trio health, flags, and last RAG sync; `/ws/runs` and `/ws/logs/{run_id}` poll every ~2s.
- Router V2: Ranks models by capabilities/latency/weight; logs routing decision to memory; calls provider adapters.
- Deployer Watchdog: Async task scans recent deployments, restarts dead processes, updates store.

Error handling & logs
- Most functions are guarded by try/except; failures fall back to safe defaults and write to `logs/*` (startup.log, errors_*.log, trio_manager.log, bridge.log, ui/usage.log, orchestrator/supervisor artifacts).

Test notes
- `tests/` cover advisor policies/health, bridge hybrid/privacy, planner/router/orchestrator E2E, memory UI/admin/embeddings/export/import, RAG retrieval/refinement, deployer registry/previews, UI websockets, dashboard routes.

---

## 5) JoJo (Qwen) vs AI Factory — Roles & Integration

Plain
- JoJo is the sovereign AI persona—a companion mind—implemented as Qwen 7B locally (with planned LoRA adapters: Identity, Truth, Tools, Strategy). The AI Factory is her operational environment and tools: memory, RAG, planning/building/evaluating, and a UI.

Technical
- JoJo’s “voice” runs through the Bridge (`ai_factory/bridge/bridge_service.py`), which applies persona and tone stabilization. Persona mode is read from `logs/ui/control_state.json`, and core identity (if present) from `ai_factory/data/doctrine/core_identity.json` via `memory_agent.load_core_identity()`.
- Delegation: The Advisor (`advisor_service.route_task`) and Router V2 (`router_v2_service`) choose local trio roles or cloud teachers. The Bridge uses external teachers via `chatgpt_proxy` for conversational enrichment; the Orchestrator uses Router V2 for task routing.

---

## 6) Native AIs (Local Trio) — Definitions & Contracts

Definitions
- Strategist AI: analytical planner; default local model via env (`AI_FACTORY_LOCAL_STRATEGIST_MODEL`, ex. `phi3:medium`).
- Memory AI: knowledge curator/context synthesizer; can be a small local LLM or deterministic logic (in practice, the Bridge and Memory agent implement deterministic context summaries).
- Executor AI: implementer/builder; local model (e.g., `phi3:mini`) and/or deterministic codegen pathways through Builder.

Invocation & health
- Advisor health check: `advisor_service.verify_local_health()` probes a single Ollama host for each role’s model (GET `/api/version` + POST `/api/generate`), with exponential backoff configurable via `AI_FACTORY_HEALTH_BACKOFF_BASE` and short timeouts.
- Trio Manager: `advisor/trio_manager.py` runs a thread that periodically probes roles and updates `app.state.trio_manager.health_map`; `/advisor/trio_health` can use this map for instant status and optional POST‑only health confirmations.

Routing & fallback
- Privacy‑strict or healthy local: prefer local; otherwise fallback to cloud (OpenAI) or degrade to mock (Bridge) to preserve UX.
- Logs: transitions written to `logs/trio_manager.log`; decisions are logged to the learning ledger (memory entries tagged `advisor_decision`).

How Trio differs from JoJo and Teachers
- Trio = native, non‑persona functional roles for local capability and privacy. JoJo = persona and companion mind. Teachers = cloud specialists for heavy reasoning/codegen.

---

## 7) Teacher Models (Cloud Specialists) — Usage & Capture

Usage
- Chat Bridge: `bridge/chatgpt_proxy.py` calls OpenAI (model “gpt‑4o”) unless mock mode; naming in bridge service mentions “GPT‑5” but is routed to gpt‑4o today.
- Router V2: `services/router_v2_service.call_model()` dispatches to provider adapters in `models/model_clients.py` (OpenAI GPT‑4o, Anthropic Claude‑3, Google Gemini). Additional teachers (Kimi K2, MiniMax M2) are planned and can be added here.

Teacher Capture Protocol (TCP) — canonical target
- Rationale: Every teacher interaction should be captured as a structured trace for later LoRA distillation and reproducible learning.
- Minimal schema (proposed):
  - `dispatch_id`, `timestamp`, `backend`, `model`, `role` (strategist/memory/executor/general)
  - `prompt`, `system_instructions`, `context_snippets[]`
  - `final_answer`, `reasoning_outline`, `assumptions[]`, `tool_calls[]`
  - `code_artifacts[]` (paths or blobs), `deployment_ops[]`, `citations[]`
  - `latency_ms`, `tokens_in`, `tokens_out`, `success`
- Storage (current vs target):
  - Current: lightweight entries in SQLite `model_usage` (counts, latency), auto‑learn text summaries in `memory_entries`, artifacts/manifests under `builds/*` and `logs/*`.
  - Target: add a `teacher_traces` table or JSONL under `data/teacher_traces/*.jsonl`; wire Router V2 and Bridge proxy to append complete traces.

---

## 8) Memory & RAG — Data Model & Operations

SQLite schema (key tables in `memory_db.py`)
- `memory_entries` (id, run_id, goal, summary, tags, score, created_at, deleted)
- `memory_links` (source_run, target_run, reason, created_at)
- `memory_feedback` (run_id, rating, notes, created_at)
- `memory_embeddings` (entry_id, vector (JSON bytes), updated_at)
- `model_usage` (run_id, step, role, backend, model, latency_ms, tokens_in, tokens_out, success, created_at)
- `dialogue_turns` (session_id, role, content, meta, timestamp)
- `dialogue_summaries` (session_id, summary, created_at)
- `mood_log` (session_id, mood, timestamp)
- `evaluation_results` (build_id, domain, passed, summary, artifacts, timestamp)

Deterministic embeddings & ranking
- When learned embeddings are unavailable, `_hash_vector(text)` in `memory_agent.py` produces a 64‑dim hash vector for consistent cosine similarity.
- `rank_memories(query, rows)` weights: semantic (default 0.6), tag overlap (0.25), recency (0.15). Tunable via env (`AI_FACTORY_MEMORY_WEIGHT_*`).

RAG pipeline (`rag_service.py`)
- Ingest: load documents or directories via `doc_loader.py`, embed with SentenceTransformers (default `all‑MiniLM‑L6‑v2`), upsert into FAISS, and persist docs/meta.
- Retrieve: encode query, search FAISS, return text+meta; reweight by MCP feedback (`memory_mcp.load_feedback_log()`; rating boosts).
- Sync with Memory MCP: pull `get_recent_memories()`, embed, upsert, persist; write UNIX timestamp to `data/vector_db/last_sync.txt`.

Sync policy (reality vs target)
- Today: on‑demand sync called by routes/scripts; no automatic background sync.
- Target: background, debounced sync triggered by new memory entries; add dedupe/TTL; expose sync stats in `/ui/system_status`. `last_sync.txt` remains the canonical observable for RAG freshness.

Privacy note
- Redaction occurs before external calls (Bridge). For PII‑at‑rest controls, consider optional storage‑level redaction for dialogue/memory entries or encrypted columns.

---

## 9) Runtime Behavior (Startup → /chat → Logging)

Startup sequence (from `main.py`)
1) `ensure_log_dir()`, `setup_logging(settings.log_level)`; banner; `init_db()`.
2) Create `deployments/`, `builds/`, `logs/`, `tests/`; rotate old orchestrator/supervisor logs.
3) `.env` validation (`validate_env`) and system audit (`run_system_audit`) → snapshot to `deployments/system_startup_audit_*.log` + `health_report_*.md`.
4) `advisor_startup_probe()` (non‑fatal). Start watchdog (`services/watchdog_service.start_watchdog`) and Trio Manager thread (`advisor/trio_manager.py`).
5) Health diagnostics; add routers; mount static; install global exception middleware; register `atexit` cleanup.

/ chat WebSocket lifecycle (`ui/chat_router.py` → `bridge_service.py`)
- Accept → greet → receive user text → echo “user” → `search_memories` → `_redact_private` → `_local_reason` (deterministic empathy) → persona/tone grounding → optional teacher call via `chatgpt_proxy` (mock by default) → merge outputs → persist dialogue/mood + auto‑learn/reflection → send “assistant”.

Resilience & fallbacks
- Mock mode default; OpenAI failures return mock responses; SQLite commits retry; FAISS absence yields safe return; advisor health failures are tolerated.

Logging & retention
- `logs/startup.log`, `logs/errors_*.log`, `logs/trio_manager.log`, `logs/bridge.log`, `logs/ui/usage.log` (token/cost + toggles), `logs/orchestrator/*`, `logs/supervisor/*`. Orchestrator/Supervisor logs pruned >30 days on startup.

---

## 10) UI / Operator Controls & Telemetry

Control panel endpoints (`ui/system_status_router.py`)
- `GET /ui/system_status`: version, milestone, trio health (via Advisor), bridge mode, flags (mock_mode, rag_enabled), RAG `last_sync` timestamp, token/cost counters.
- `GET/POST /ui/control_state`: get/set persona mode (stored in `logs/ui/control_state.json`).
- `POST /ui/toggle_mock`, `POST /ui/toggle_rag`: flip runtime flags; appended to `logs/ui/usage.log`.

Dashboards & views (`ui/*`)
- System health, memory insights, analytics, runs/history, RAG dashboard; static assets under `/static`.

WebSockets (`ui/ws_router.py`)
- `/ws/runs`: send recent runs, then poll for additions.
- `/ws/logs/{run_id}`: poll orchestrator/supervisor logs for changes and stream updates.
- Planned evolution: event‑driven updates to replace polling.

---

## 11) Version/Phase State — Reality vs Target

Current values (multiple sources)
- `ai_factory/version.py`: `__version__ = "v3.5.2-rational-core"`, `PHASE = "3.5.2"`, `__milestone__ = "Rational Core Alignment + MCP Sync"`.
- Root `VERSION`: `v3.2.6-TCE` (legacy).
- `/health` handler in `main.py`: returns `version = "v2.0-cognitive-engine"` (hardcoded string).
- Phase markers: latest `logs/_codex_phase.marker` entries show `5.1-b start/complete` and `4.0-R rag-perfection` with detailed notes; commit history shows “4.9 Structural Rebirth”.

Recommendation (single source of truth)
- Use `ai_factory/version.py` as canonical. Update `main.py`’s `FastAPI(... version=...)`, `/health` response version, UI surfaces, and any templates to read from `ai_factory/version.py` (imported at module load) to eliminate drift.

---

## 12) Current Status (Checkpoint v4.9)

Subsystems
- Advisor, Bridge, Memory, RAG, MCP, Planner, Builder, Evaluator, Orchestrator, Deployer, UI, Router V2, Supervisor: functionally complete and tested.
- Partial: Teacher capture store (structured traces) not yet implemented; RAG background sync absent; version unification pending; websockets use polling.

Recent work
- 4.0‑R: feedback‑weighted retrieval; memory sync; safe retries; self‑evaluation; RAG UI. 4.9: structural cleanup; enhanced system status; repository hygiene.

---

## 13) Roadmap (Near → Mid)

v5.0 — Hybrid Intelligence Initiation
- Version unification across app surfaces (import `ai_factory/version.py`).
- Background, debounced RAG sync on new memory entries; add dedupe/TTL; expose sync metrics in `/ui/system_status`.
- Central runtime state manager (SQLite or small KV) for flags/persona/usage (replacing globals and ad‑hoc files); audit‑ready state transitions.
- Teacher Capture Store: `teacher_traces` (DB table) or `data/teacher_traces/*.jsonl`; wire Bridge proxy and Router V2 to append TCP records.
- Advisor health cache with expiry; model_usage‑aware routing decisions.

v6.x — Event‑Driven Telemetry & State Bus
- Replace WS polling with server‑side events or an internal event bus; emit orchestrator/supervisor/advisor events for UI.
- Incremental state snapshots for dashboards; alerting on degraded health.

v7.x — Teacher Distillation & Local Strategist Upgrade
- LoRA training pipelines for Identity/Truth/Tools/Strategy from teacher traces; periodic refresh.
- Strategist/Memory/Executor synergy with richer contracts (e.g., schema‑checked outputs, tool invocation, codegen constraints).

Indicative file/module changes
- `main.py` (version unification), `ui/system_status_router.py` (sync metrics), `memory_agent.py` + `rag_service.py` (background sync hooks), new `services/state_store.py`, new `models/teacher_traces.py` + `services/teacher_capture.py`, `ui/ws_router.py` (event bus), `advisor/advisor_service.py` (health cache + usage‑aware policy).

---

## 14) Operational Playbooks (How‑To)

Start Factory (programmatic)
```bash
python -m ai_factory.main
# The app auto‑selects a free port in 8015–8050; logs to logs/startup.log
```

Run with Uvicorn (explicit)
```bash
uvicorn ai_factory.main:app --host 127.0.0.1 --port 8015 --log-level info
```

Toggle mock/live and RAG
```bash
# Mock mode (default True) and RAG (default True)
curl -X POST http://127.0.0.1:8015/ui/toggle_mock
curl -X POST http://127.0.0.1:8015/ui/toggle_rag
```

Set persona mode
```bash
curl -X POST http://127.0.0.1:8015/ui/control_state \
  -H 'Content-Type: application/json' \
  -d '{"persona_mode": "strategist"}'
```

Kick off an orchestrator run
```bash
curl -X POST http://127.0.0.1:8015/orchestrator/run \
  -H 'Content-Type: application/json' \
  -d '{"goal": "build a small FastAPI app", "deploy": false}'
```

RAG ingestion (service‑level)
```python
from ai_factory.rag import rag_service as rag
rag.ingest_document('path/to/docs_or_dir')
rag.sync_with_memory_mcp(limit=200)
```

Export memories / inspect
- SQLite at `ai_factory/data/memory.db` (schema in `memory_db.py`).
- Exports under `ai_factory/data/exports/*` (created by scripts / evaluators).

Stress tests and audits
- Scripts: `scripts/stress_test_factory.py`, `scripts/factory_diagnostics.py`, `scripts/self_evaluate.py`, PowerShell helpers under `scripts/*.ps1`.

---

## 15) Security, Privacy, and Cost

- Redaction scope: `_redact_private()` masks API keys, personal Windows paths, and emails before any external call; extendable.
- Privacy‑first routing: Advisor favors local trio; mock mode default prevents unintentional cloud use.
- Cost tracking: `chatgpt_proxy` estimates token cost and appends to `logs/ui/usage.log`; Control Panel shows aggregated tokens/USD.
- PII at rest: dialogue/memory stored in SQLite. Consider optional storage redaction/encryption for sensitive deployments; add per‑record redaction policy and secure exports.

---

## 16) Testing & Quality

- Run tests (pytest configured in `pyproject.toml`):
```bash
pytest -q
```
- Coverage focus: Advisor policies/health (`tests/test_advisor_*`), Bridge hybrid and privacy (`tests/test_bridge_*`, `tests/test_hybrid_routing_privacy.py`), Planner/Router/Orchestrator E2E, Memory UI/admin/embeddings/export/import, RAG refinement, Deployer previews, UI websockets, dashboard routes, startup/health.
- Deterministic CI: planner stub, mock mode default, shortened timeouts under `PYTEST_CURRENT_TEST`, and deterministic embeddings ensure stable tests.

---

## 17) Essence Summary (3 sentences)

AI Factory Builder is a resilience‑first environment where JoJo (Qwen 7B) speaks through a safe, hybrid Bridge, routes via a privacy‑aware Advisor, and learns through a dual memory system that’s explainable and testable. The Factory turns goals into artifacts with a plan→build→evaluate→deploy loop, logging everything for visibility and future teacher distillation. Next, it unifies versioning, adds background RAG sync and teacher capture, and evolves toward event‑driven telemetry and LoRA‑based native intelligence.

---

Appendix: Source Evidence Map (selected)
- App and routers: `ai_factory/main.py` (lifespan, middleware, router includes, static mount)
- Advisor: `ai_factory/advisor/advisor_service.py`, `advisor/advisor_router.py`, `advisor/trio_manager.py`
- Bridge: `ai_factory/bridge/bridge_service.py`, `bridge/chatgpt_proxy.py`
- Memory: `ai_factory/memory/memory_agent.py`, `memory/memory_db.py`, `memory/routers/memory_router.py`
- RAG: `ai_factory/rag/rag_service.py`, `rag/vector_db.py`, `rag/doc_loader.py`
- Orchestrator: `ai_factory/orchestrator/orchestrator_agent.py`, `orchestrator/orchestrator_router.py`, `orchestrator/orchestrator_store.py`
- UI: `ai_factory/ui/*` routers/templates/static; websockets in `ui/ws_router.py` and `ui/chat_router.py`
- Deployer/Watchdog: `ai_factory/deployer/*`, `services/watchdog_service.py`
- Config/Flags: `ai_factory/config.py`, `ai_factory/config_runtime_flags.py`
- Version/Phases: `ai_factory/version.py`, `root VERSION`, `logs/_codex_phase.marker`, recent `git log`

