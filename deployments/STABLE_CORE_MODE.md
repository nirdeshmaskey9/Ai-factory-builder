# Stable Core Mode

This repository is locked to Stable Core Mode for:

- Version: v1.3-gpt4o-builder
- Tag: v1.3-stable-core
- Status: Verified by self-verify and system audit

Do not modify core service contracts without updating the stable tag.

## Resilient Startup: Auto Port Recovery (v1.4.2)

In environments where the default API port may already be in use, the Factory can now auto-select a free port.

- Range: 8015..8050
- Strategy: Attempts 8015 first; on bind failure (e.g., Windows `[WinError 10048]` or Linux/macOS `OSError [Errno 98]`), increments until a free port is found.
- Logging:
  - Appends the selected port to `logs/startup.log` as `selected_port {port}`
  - Prints to console: `✅ Port {port} selected — Factory online` (falls back to ASCII if terminal does not support Unicode)
- Cross-platform: Works on Windows, macOS, and Linux.

How to launch with auto recovery:

- Prefer programmatic entrypoint which includes port recovery:
  - `python -m ai_factory.main`

Notes:
- If you continue to start via uvicorn CLI directly (e.g., `python -m uvicorn ai_factory.main:app --port 8015`), uvicorn will attempt the specified port and will not use auto recovery. Use the programmatic entrypoint above for resilience.

### Quick Launch (v1.4.3)
You can now start the Factory with one command:

```bash
python scripts/run_factory.py
```
