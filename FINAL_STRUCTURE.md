# AI Factory Builder - Final Directory Structure

```
ai_factory_builder/
│
├── artifacts/                    # Archived and generated files
│
├── data/                         # Unified data directory
│   ├── app-internal/            # Application-internal data
│   │   ├── backups/            # Database backups (40+ files)
│   │   ├── chroma/             # Vector database storage
│   │   ├── doctrine/           # Core identity/config
│   │   │   └── core_identity.json
│   │   ├── exports/            # Memory exports (67 files: 46 JSON, 21 CSV)
│   │   ├── logs/               # App-specific logs (7 files)
│   │   └── snapshots/          # Event snapshots
│   │       └── events_20251015T234826Z.jsonl
│   ├── memory/                  # User memory data
│   │   └── feedback_log.json
│   ├── personal/               # User profiles
│   │   ├── jojo_identity.txt
│   │   └── nirdesh_profile.txt
│   ├── vector_db/              # Vector database files
│   │   ├── docs.txt
│   │   ├── index.faiss
│   │   ├── last_sync.txt
│   │   └── meta.json
│   ├── feedback.db             # Feedback database
│   ├── health.log              # Health logs
│   ├── memory.db               # Main memory database
│   └── user_snapshot.json      # User snapshots
│
├── deployments/                 # Runtime deployments (1712 files)
│   ├── [569 *.py files]
│   ├── [481 *.md files]
│   └── [368 *.log files]
│
├── docs/                        # Documentation
│   ├── AI_FACTORY_CANONICAL_REFERENCE.md
│   ├── ARCHITECTURE.md
│   ├── MIGRATION_v1.2-master.md
│   ├── NEXT.md
│   ├── PHASES.md
│   ├── README.md
│   └── milestones/             # Version milestones (15 files)
│
├── logs/                        # Runtime logs
│   ├── ARCHIVE/
│   ├── _milestones/
│   ├── orchestrator/           # Orchestrator logs (1308 JSON files)
│   ├── supervisor/             # Supervisor logs (654 JSON files)
│   ├── ui/                     # UI logs
│   └── [various log files]
│
├── scripts/                     # Utility scripts
│   ├── icons/
│   ├── check_local_trio.ps1
│   ├── check_local_trio.sh
│   ├── cleanup_logs.py
│   ├── factory_autocheck.py
│   ├── factory_diagnostics.py
│   ├── run_app.py
│   ├── run_factory.py
│   └── [20+ other scripts]
│
├── src/                         # Source code (NEW - src layout)
│   └── ai_factory/             # Main package
│       ├── __init__.py
│       ├── main.py             # Application entry point
│       ├── version.py
│       ├── config.py
│       ├── config_env_validator.py
│       ├── config_runtime_flags.py
│       ├── logging_setup.py
│       ├── model_registry.json
│       │
│       ├── advisor/            # Advisor module
│       ├── bridge/             # Bridge module
│       ├── builder/            # Builder module
│       ├── builders/           # Builder implementations
│       ├── compat/             # Compatibility layer
│       ├── config/             # Configuration
│       ├── core/               # Core utilities
│       ├── debugger/           # Debugger module
│       ├── deployer/           # Deployer module
│       ├── evaluator/          # Evaluator module
│       ├── evaluator_v2/       # Evaluator v2
│       ├── memory/             # Memory module
│       ├── models/             # Model clients
│       ├── mood/               # Mood engine
│       ├── orchestrator/       # Orchestrator module
│       ├── planner/            # Planner module
│       ├── rag/                # RAG module
│       ├── router_v2/          # Router v2
│       ├── routers/            # Core routers
│       ├── services/           # Service layer
│       ├── supervisor/         # Supervisor module
│       ├── system/             # System utilities
│       ├── template_bank/      # Template registry
│       ├── templates/          # Application templates
│       ├── testing/            # Testing utilities
│       ├── tools/              # Tools
│       └── ui/                 # UI module
│           ├── static/         # Static assets (25 files)
│           └── templates/     # UI templates (27 HTML files)
│
├── tests/                       # All tests (consolidated)
│   ├── __init__.py
│   ├── stress_tester.py        # Moved from ai_factory/tests/
│   ├── stress_suite/
│   └── [80+ test files]
│
├── .gitignore
├── CHANGELOG.md
├── poetry.lock
├── pyproject.toml              # Updated: pythonpath = ["src", "."]
├── pytest.ini                  # Updated: pythonpath = src .
├── README.md
├── requirements.txt
├── requirements-lock.txt
└── VERSION
```

## Key Changes Summary

### Removed
- ❌ `archive_legacy/` - Legacy code
- ❌ `builds/` - Outdated builds
- ❌ `chromadb/` - Redundant module
- ❌ `project_structure.txt` - Large generated file
- ❌ `scatter.png` - Generated visualization
- ❌ `ai_factory/tests/` - Consolidated

### Moved/Restructured
- ✅ `ai_factory/` → `src/ai_factory/` (src layout)
- ✅ `ai_factory/data/` → `data/app-internal/` (unified data)
- ✅ `ai_factory/tests/stress_tester.py` → `tests/stress_tester.py`

### Created
- ✅ `artifacts/` - For archived/generated files
- ✅ `data/app-internal/` - App-internal data structure

### Updated
- ✅ All hardcoded paths in source code
- ✅ `pyproject.toml` - pythonpath configuration
- ✅ `pytest.ini` - pythonpath configuration
- ✅ Import paths remain `from ai_factory.*` (no code changes needed)

---

**Structure normalized and modernized. All functionality preserved.**

