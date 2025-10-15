# AI Factory Builder — Phase 1: Router Core

Local FastAPI hub that routes requests to models/tools (stubbed for now).

## Features (Phase 1 DoD)

- ✅ `uvicorn ai_factory.main:app --reload` starts.
- ✅ `GET /healthcheck` returns JSON.
- ✅ `POST /planner/dispatch` accepts `{prompt, task_type}` and returns structured JSON (stubbed).
- ✅ Logs written to `ai_factory/data/logs/app.log`.
- ✅ README + curl + pytest tests.

## Project Layout



ai_factory_builder/
.env.example
requirements.txt
pyproject.toml
ai_factory/
...
tests/
docs/ 
