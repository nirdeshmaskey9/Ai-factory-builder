# v3.2.1 — Local Trio Stabilization

- Hardened local launcher scripts for Windows (PowerShell) and Linux/macOS (bash)
- Added quick health check scripts `check_local_trio` for both shells
- Advisor startup diagnostics: logs local trio health per role
- Factory info now includes `local_trio_health` summary
- All tests pass

## Scripts
- `scripts/run_local_trio.ps1` / `.sh`: start three `ollama serve --port` instances, health-check `/api/version`
- `scripts/check_local_trio.ps1` / `.sh`: verify health of trio

## Advisor
- `advisor_service.startup_probe()` logs: Strategist/Memory/Executor health

## Version
- VERSION: `v3.2.1-local-trio-stabilization`

