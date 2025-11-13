# 🧠 AI Factory Builder — v3.9.4.1 Architecture

**JoJo Planet — Unified Identity, Stable Memory, Clean Hybrid Output**

This document describes the current system architecture at v3.9.4.1. The platform is a local-first FastAPI application featuring JoJo, a unified AI companion with persistent memory, hybrid reasoning (local + cloud), and clean conversational output.

---

## 🧩 High-Level Overview

- **App server**: FastAPI + Uvicorn (port 8000 enforced)
- **Configuration**: Pydantic Settings (env-driven), local `.env`
- **Logging**: Console + rotating file (under `logs/app.log`)
- **Storage**:
  - SQLite database: `data/memory.db` (persistent memory storage)
  - Chroma vector store: `data/app-internal/chroma/` (optional semantic search)
  - FAISS index: `data/vector_db/index.faiss` (alternative vector index)
- **Local AI**: Ollama with Local Trio models (Strategist, Memory, Executor)
- **External AI**: Optional cloud model (GPT-4o) for final enrichment
- **Tests**: `pytest` covering health, memory persistence, bridge service, and UI routes

---

## 🧠 Core Components

### 1. JoJo Unified Identity Layer

**Location**: `src/ai_factory/identity/jojo_identity.py`

JoJo is a unified AI companion with a single, consistent identity:
- **Name**: JoJo
- **Creator**: Nirdesh
- **Purpose**: Lifelong AI companion, assistant, problem-solver, and evolving partner
- **Voice**: Warm, intelligent, emotionally aware, grounded, loyal

**Key Functions**:
- `get_identity_prompt()` - System prompt for identity injection
- `build_identity_system_prompt()` - Full system prompt builder
- `build_identity_context_for_local()` - Local reasoning context
- `get_external_enrichment_context()` - External model context

**Integration**: Identity is injected into every hybrid reasoning chain, ensuring consistent persona across all interactions.

---

### 2. Hybrid Reasoning Pipeline (Bridge Service)

**Location**: `src/ai_factory/bridge/bridge_service.py`

The bridge service implements a memory-first hybrid reasoning pipeline:

**Execution Order**:
1. **Memory Retrieval FIRST** - Retrieve relevant user memories before any model runs
2. **System Prompt Building** - Build prompt with identity + memory context
3. **Local Reasoning** - Generate rough draft using local models (optional)
4. **External Enrichment** - External model provides final authoritative answer (OVERRIDES local)
5. **Clean Output** - Apply `clean_output()` filter to remove all debug noise
6. **Return** - Return clean, unified response

**Key Functions**:
- `process_bridge_chat()` - Main hybrid reasoning pipeline
- `call_gpt5()` - External model wrapper
- `_local_reason()` - Deterministic local reasoning (lightweight)

**Filter Chain**: `src/ai_factory/bridge/filter_chain.py`
- `clean_output()` - Final clean filter (removes `[Local]`, `[External]`, memory IDs, transcript spam)
- `filter_output()` - Robust pattern matching for noise removal

---

### 3. Persistent Memory System

**Location**: `src/ai_factory/memory/`

#### Memory Database (`memory_db.py`)
- **SQLite**: `data/memory.db`
- **Tables**:
  - `memory_entries` - Core memory storage (goal, summary, tags, score)
  - `memory_events` - Planner dispatch events
  - `memory_links` - Memory relationships
  - `memory_embeddings` - Vector embeddings (optional)
  - `dialogue_turns` - Conversation history
  - `mood_logs` - Emotional state tracking

#### Memory Agent (`memory_agent.py`)
- `store_memory()` - Store new memories (commits to SQLite)
- `search_memories()` - Text-based search with ranking
- `rank_memories()` - Semantic + tag + recency ranking
- `stats()` - Memory statistics

#### Identity Seeder (`identity_seeder.py`)
- **Purpose**: Ensures core identity memories exist on startup
- **Memories Seeded**:
  - User full name: "Nirdesh Maskey"
  - Birthdate: "July 8, 2001"
  - Birthplace: "Kathmandu, Nepal"
  - Country: "Nepal"
  - Current location, profession, education
- **Idempotent**: Only creates if missing, skips if exists

#### Vector Store (`memory_embeddings.py`)
- **ChromaDB**: Persistent vector store at `data/app-internal/chroma/`
- **Fallback**: In-memory collection if ChromaDB unavailable
- **Embeddings**: SentenceTransformer (all-MiniLM-L6-v2) or hash-based fallback

---

### 4. Local Trio Models (Advisor)

**Location**: `src/ai_factory/advisor/`

Three specialized local AI models managed via Ollama:

- **Strategist** (`qwen2:1.5b-instruct-q4_K_M`)
  - Purpose: Optimized reasoning
  - VRAM: ~900 MB
  
- **Memory** (`mistral:7b-instruct-v0.3-q4_K_M`)
  - Purpose: Contextual synthesis
  - VRAM: ~4200 MB
  
- **Executor** (`phi3:mini`)
  - Purpose: Code execution
  - VRAM: ~2400 MB

**Total VRAM**: ~7.5 GB (within 8GB limit)

**Management**:
- `local_trio.py` - Model definitions and registry
- `trio_manager.py` - Health monitoring
- `advisor_service.py` - Task routing and health checks

---

### 5. Web Interface (UI)

**Location**: `src/ai_factory/ui/`

#### Chat Interface (`/chat`)
- **Template**: `templates/chat.html`
- **WebSocket**: Real-time bidirectional communication
- **Features**:
  - Clean message display (no debug noise)
  - System status sidebar
  - Local trio health display
  - Unified JoJo identity

#### Memory Viewer (`/ui/memory`)
- **Template**: `templates/memory.html`
- **Features**:
  - Browse all memories
  - Search functionality
  - Memory statistics
  - Tailwind CSS styling

#### System Status (`/ui/system_status`)
- **Features**:
  - Local trio health (compact table)
  - System metrics
  - Model information

#### Debug Endpoints (`/debug/memory/*`)
- `GET /debug/memory/list` - List all memories (id, key, value, tags)
- `GET /debug/memory/search?q=...` - Search memories (case-insensitive LIKE)

---

## 🔄 Data Flow

### Chat Request Flow

```
User Input
    ↓
1. Memory Retrieval (search_memories)
    ↓
2. Build System Prompt (identity + memory context)
    ↓
3. Local Reasoning (rough draft, optional)
    ↓
4. External Model (final authoritative answer)
    ↓
5. Clean Output (remove debug noise)
    ↓
6. Return Clean Response
```

### Memory Storage Flow

```
Memory Store Request
    ↓
1. Validate Input
    ↓
2. Create MemoryEntry
    ↓
3. Commit to SQLite (data/memory.db)
    ↓
4. (Optional) Index to ChromaDB
    ↓
5. Return Memory ID
```

### Startup Sequence

```
1. Initialize Database (init_db)
    ↓
2. Database Ping (db_ping) - Verify connection
    ↓
3. Seed Identity Memories (seed_identity_memories)
    ↓
4. Initialize Local Trio Manager
    ↓
5. Start FastAPI Application
```

---

## 🗄️ Storage Layout

### SQLite Database (`data/memory.db`)

**Tables**:
- `memory_entries` - Core memory storage
  - `id` (PK), `run_id`, `goal`, `summary`, `tags`, `score`, `created_at`, `deleted`
- `memory_events` - Planner dispatch events
- `memory_links` - Memory relationships
- `dialogue_turns` - Conversation history
- `dialogue_summaries` - Session summaries
- `mood_logs` - Emotional state tracking
- `supervisor_sessions` - Orchestration sessions
- `debugger_runs` - Code execution results
- `evaluation_results` - Evaluation outcomes

### Vector Store (`data/app-internal/chroma/`)
- Persistent ChromaDB collection
- Falls back to in-memory if unavailable

### Logs (`logs/`)
- `app.log` - Application logs
- `bridge.log` - Bridge service logs
- `memory.log` - Memory diagnostics
- `startup.log` - Startup events

---

## 📁 Repository Structure

```
ai_factory_builder/
├── src/ai_factory/              # Main application code
│   ├── bridge/                  # Hybrid reasoning pipeline
│   │   ├── bridge_service.py   # Main hybrid pipeline
│   │   ├── filter_chain.py     # Output cleaning
│   │   ├── chatgpt_proxy.py    # External model proxy
│   │   └── response_manager.py # Response integration
│   ├── memory/                  # Memory system
│   │   ├── memory_db.py        # SQLite models & engine
│   │   ├── memory_agent.py     # Memory operations
│   │   ├── identity_seeder.py  # Identity memory seeding
│   │   ├── memory_embeddings.py # Vector store
│   │   └── routers/            # Memory API routes
│   ├── identity/                # JoJo unified identity
│   │   └── jojo_identity.py    # Identity definitions
│   ├── advisor/                 # Local trio management
│   │   ├── local_trio.py       # Model definitions
│   │   ├── trio_manager.py     # Health monitoring
│   │   └── advisor_service.py  # Task routing
│   ├── ui/                      # Web interface
│   │   ├── chat_router.py      # Chat UI
│   │   ├── memory_ui_router.py # Memory viewer
│   │   ├── system_status_router.py # Status display
│   │   └── templates/          # Jinja2 templates
│   ├── config.py                # Application settings
│   └── main.py                  # FastAPI app entry point
├── data/                         # Runtime data
│   ├── memory.db                # SQLite database
│   └── app-internal/            # Internal app data
│       └── chroma/              # ChromaDB vector store
├── scripts/                      # Utility scripts
│   ├── run_factory.py           # Main launcher
│   ├── setup_ollama.ps1        # Ollama setup (Windows)
│   ├── setup_ollama.sh         # Ollama setup (Linux/Mac)
│   ├── validate_trio.ps1       # Trio validation
│   └── memory_diagnostics.py    # Memory diagnostics
├── tests/                        # Test suite
│   └── test_memory_persistence.py # Memory tests
├── docs/                         # Documentation
└── logs/                         # Application logs
```

---

## 🔌 Runtime Integration

### Startup Sequence (`main.py`)

1. **Initialize Logging** - Setup console + file logging
2. **Initialize Database** - `init_db()` creates tables
3. **Database Ping** - `db_ping()` verifies connection
4. **Seed Identity Memories** - `seed_identity_memories()` ensures core memories exist
5. **Initialize Local Trio** - Health check for Ollama models
6. **Mount Routers** - All API routes registered
7. **Start FastAPI** - Application ready on port 8000

### Middleware

- **MemoryLoggerMiddleware** - Logs planner events to memory
- **DebugLoggerMiddleware** - Timing headers for debugger routes
- **GlobalExceptionMiddleware** - Global error logging

### Routers

- `/chat` - Chat interface (WebSocket)
- `/ui/memory` - Memory viewer
- `/ui/system_status` - System status
- `/debug/memory/list` - Debug memory list
- `/debug/memory/search` - Debug memory search
- `/memory/*` - Memory API routes
- `/bridge/*` - Bridge service routes
- `/advisor/*` - Advisor routes

---

## 🚀 Usage Examples

### Start Application

```bash
python scripts/run_factory.py
```

### Chat Interface

Visit: `http://127.0.0.1:8000/chat`

**Example Queries**:
- "Who am I?" → Recalls: "You are Nirdesh Maskey"
- "When was I born?" → Recalls: "July 8, 2001"
- "Where was I born?" → Recalls: "Kathmandu, Nepal"
- "Which country am I from?" → Recalls: "Nepal"

### Memory API

```bash
# List memories
curl "http://127.0.0.1:8000/debug/memory/list?limit=10"

# Search memories
curl "http://127.0.0.1:8000/debug/memory/search?q=birth"

# Memory stats
curl "http://127.0.0.1:8000/memory/stats"
```

### Setup Ollama Models

```bash
# Windows
.\scripts\setup_ollama.ps1

# Linux/Mac
./scripts/setup_ollama.sh
```

### Run Diagnostics

```bash
python scripts/memory_diagnostics.py
```

---

## 🔒 Local-First Principles

- **No External Dependencies Required**: Works offline with local models
- **Graceful Fallbacks**: ChromaDB → in-memory, SentenceTransformer → hash embeddings
- **Persistent Storage**: All data stored locally in `data/` directory
- **Privacy-First**: No data sent externally unless explicitly configured

---

## ✅ Test Coverage

- `tests/test_memory_persistence.py` - Memory persistence tests
- `tests/test_health.py` - Health check tests
- `tests/test_planner.py` - Planner tests
- `tests/test_memory_log.py` - Memory logging tests
- `tests/test_memory_search.py` - Memory search tests

---

## 📌 Version

- **Current Version**: v3.9.4.1-nl
- **Milestone**: Unified JoJo Identity - Final Cleanup + Hybrid Brain
- **Phase**: 3.9.4.1

---

## 🧭 What's Next

- **Phase 4.0**: Emotional Engine & Identity Layer Expansion
  - Enhanced emotional awareness
  - Deeper identity integration
  - Advanced memory-powered features
  - Emotional state tracking and response

---

## 🔗 Related Documentation

- **Phases**: See `docs/PHASES.md` for phase history
- **Phase 3.9.x Details**: See `PHASE_3.9.4_SUMMARY.md` and related phase documents
- **Local Trio**: See `LOCAL_TRIO_STATUS.md`
- **Hybrid Brain**: See `HYBRID_BRAIN_READINESS.md`
