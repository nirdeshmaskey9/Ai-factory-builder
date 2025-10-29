# v3.2.2 — Local Trio Fix

Fixes
- PowerShell launcher now uses per-port OLLAMA_HOST + `ollama run` per role (resolves `unknown flag: --port`).
- PowerShell health checker fixed (string terminator issue) and outputs UTF-8 safely.

Testing
- Added `tests/test_local_trio_fix.py` to execute `scripts/check_local_trio.ps1` under PowerShell with ExecutionPolicy Bypass.

Version
- VERSION bumped to `v3.2.2-local-trio-fix`.

