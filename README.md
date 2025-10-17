# AI Factory Builder — v1.1 Self-Healing

This release adds:
- Startup self-audit with console summary and logs
- .env validator (non-fatal) ensuring key presence and directories
- PID tracking for deployments and safer rollback
- Watchdog to auto-restart crashed deployments
- /factory/info route with version and health

Start the server:

  poetry run uvicorn ai_factory.main:app --reload --port 8015

Stress test and audit:

- GET /orchestrator/stress?n=5
- python -m ai_factory.tools.system_audit

Info:

- GET /factory/info
