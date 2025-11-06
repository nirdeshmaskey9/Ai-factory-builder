# Cleanup Overview — Phase 4.9

Purpose: structural rebirth & clean rebase without loss.

What moved to `archive_legacy/`:
- `dashboard/` — legacy milestone data (unused by app).
- `ui_templates/` — old UI templates for `ui_server.py` (replaced by `ai_factory/ui/templates`).
- `ui_server.py` — legacy standalone server not used by main app.
- `tmp_main_copy.py`, `tmpnull` — temporary files from previous phases.

What stayed (core):
- `ai_factory/` — all active modules (advisor, bridge, memory, rag, ui, orchestrator, router_v2, etc.).
- `tests/` — full test suite unchanged.
- `scripts/` — utilities and stress testing scripts.
- `requirements.txt`, `ai_factory/main.py`, `ai_factory/version.py`.

Notes:
- Kept vendored `chromadb/` because `ai_factory/memory/memory_embeddings.py` imports it.
- Kept `ai_factory/tests/stress_tester.py` because orchestrator imports it.
- No import paths changed; active routes and modules are unaffected.

Final layout (top-level excerpt):
- `ai_factory/`
- `archive_legacy/`
  - `dashboard/`
  - `ui_templates/`
  - `ui_server.py`
  - `tmp_main_copy.py`
  - `tmpnull`
- `builds/`
- `data/`
- `deployments/`
- `docs/`
- `logs/`
- `scripts/`
- `tests/`
- `requirements.txt`
- `pyproject.toml`
- `README.md`
