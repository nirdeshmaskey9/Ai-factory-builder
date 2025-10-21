# Changelog

## v1.2-master
- Add domain detector and modular builders for `web`, `cli`, `ml`.
- Add `POST /factory/create` route and ADR logging.
- Add evaluator suites per domain and a runner.
- Preserve watchdog, PID tracking, env validator, and orchestrator.

## v1.2-master-stable
- Core hardening: atomic manifest writes, template fallbacks, evaluator summary fallback.
- Memory MCP: evaluation results persisted to SQLite with retries + diagnostics.
- Health: /factory/info extended with timestamp and MCP summary.
- Startup/shutdown logs and global exception logging middleware.
- Planner: domain blueprint helper + regression tests.
- Scripts: Factory diagnostics (to be run manually) added.
