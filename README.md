# AI Factory Builder - v1.2-master Universal Builder

This release adds domain-aware creation with full audit/rollback:
- Startup self-audit with console summary and logs
- .env validator (non-fatal) ensuring key presence and directories
- PID tracking for deployments and safer rollback
- Watchdog to auto-restart crashed deployments
- /factory/info route with version and health
- POST /factory/create for Universal Builder (web, cli, ml)

Start the server:

  poetry run uvicorn ai_factory.main:app --reload --port 8015

Stress test and audit:

- GET /orchestrator/stress?n=5
- python -m ai_factory.tools.system_audit

Info:

- GET /factory/info (version: 1.2-master)
- POST /factory/create
