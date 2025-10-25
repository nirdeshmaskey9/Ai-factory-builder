#!/usr/bin/env bash
set -euo pipefail

echo "Starting server (background)"
uvicorn ai_factory.main:app --reload &
PID=$!
sleep 2

echo "Create a couple orchestrator-like runs (simulated via planner)"
curl -s -X POST http://127.0.0.1:8000/planner/dispatch -H 'Content-Type: application/json' -d '{"prompt":"Build a FastAPI app","task_type":"coding"}' >/dev/null || true
curl -s -X POST http://127.0.0.1:8000/planner/dispatch -H 'Content-Type: application/json' -d '{"prompt":"Create a CLI tool","task_type":"coding"}' >/dev/null || true

echo "Trigger learning"
curl -s -X POST http://127.0.0.1:8000/memory/learn -H 'Content-Type: application/json' -d '{}' | jq .

echo "Open dashboard: /dashboard/memory?q=fastapi"
echo "Visit: http://127.0.0.1:8000/dashboard/memory?q=fastapi"

echo "Stats:"
curl -s http://127.0.0.1:8000/memory/stats | jq .

kill $PID || true

