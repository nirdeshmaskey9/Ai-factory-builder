# v3.2.3 — Local Trio Auto-Manager

Features
- Auto-launch local trio (Ollama serve) on startup
- Monitors health every 60s and restarts crashed instances
- Exposes live status via `/advisor/trio_health` and `/factory/info`
- Dashboard shows local trio health with auto-refresh

Implementation
- `ai_factory/advisor/trio_manager.py` with background monitor (thread)
- Wired in `ai_factory/main.py` lifespan to start/stop manager
- `ai_factory/advisor/advisor_router.py` adds `/advisor/trio_health`
- `ai_factory/routers/factory_info.py` includes `local_trio_health`
- `ai_factory/ui/templates/dashboard/index.html` renders trio status
- `.env.example` includes STRATEGIST_*/MEMORY_*/EXECUTOR_* defaults

Tests
- `tests/test_trio_manager.py` mocks subprocess and HTTP and asserts restart + endpoint
- `tests/test_advisor_trio_health_endpoint.py` asserts roles present

Version
- VERSION: `v3.2.3-local-trio-auto-manager`

