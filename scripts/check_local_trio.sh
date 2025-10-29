#!/bin/bash
echo "🔍 Checking local trio health..."
for port in 11434 11435 11436; do
  if curl -s http://127.0.0.1:$port/api/version >/dev/null; then
    echo "✅ Port $port OK"
  else
    echo "⚠️ Port $port not responding"
  fi
done

