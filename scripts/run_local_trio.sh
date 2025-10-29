#!/bin/bash
echo "🚀 Launching local AI trio..."
if [ "$DRY_RUN" = "1" ]; then
  echo "[DRY_RUN] Skipping actual ollama serve launches."
  exit 0
fi
nohup ollama serve --port 11434 >/dev/null 2>&1 &
nohup ollama serve --port 11435 >/dev/null 2>&1 &
nohup ollama serve --port 11436 >/dev/null 2>&1 &

sleep 5
for port in 11434 11435 11436; do
  if curl -s http://127.0.0.1:$port/api/version >/dev/null; then
    echo "✅ Port $port healthy"
  else
    echo "❌ Port $port unreachable"
  fi
done

