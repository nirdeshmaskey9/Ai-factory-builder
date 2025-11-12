#!/bin/bash
# ===============================
# 🧠 Ollama Setup Script
# AI Factory Builder v3.7.0 - Hybrid Brain Upgrade
# Hardware: Alienware m18 R2 (8GB VRAM / 32GB RAM)
# ===============================

echo "🧠 AI Factory Builder - Ollama Local Trio Setup"
echo "Phase: v3.7.0-hybrid-brain-initialization"
echo ""

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama not found. Please install Ollama first:"
    echo "   https://ollama.ai/download"
    exit 1
fi

echo "✅ Ollama found: $(which ollama)"
echo ""

# Verify Ollama is running
echo "🔍 Checking Ollama daemon..."
if curl -s http://127.0.0.1:11434/api/version > /dev/null 2>&1; then
    VERSION=$(curl -s http://127.0.0.1:11434/api/version | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
    echo "✅ Ollama daemon running (version $VERSION)"
else
    echo "⚠️  Ollama daemon not running. Please start it:"
    echo "   ollama serve"
    exit 1
fi

echo ""
echo "📦 Pulling Local Trio models (optimized for 8GB VRAM)..."
echo ""

# Local Trio v5 Models
declare -a models=(
    "qwen2:1.5b-instruct-q4_K_M|Strategist|Optimized reasoning|~900MB"
    "mistral:7b-instruct-v0.3-q4_K_M|Memory|Contextual synthesis|~4.2GB"
    "phi3:mini-4k-instruct-q4_K_M|Executor|Code execution|~2.4GB"
)

for model_info in "${models[@]}"; do
    IFS='|' read -r name role purpose vram <<< "$model_info"
    echo "📥 Pulling $role model: $name ($vram)..."
    START_TIME=$(date +%s)
    
    if ollama pull "$name"; then
        END_TIME=$(date +%s)
        DURATION=$((END_TIME - START_TIME))
        echo "   ✅ $role model ready (${DURATION}s)"
    else
        echo "   ❌ Failed to pull $name"
    fi
    echo ""
done

echo "🔍 Verifying installed models..."
ollama list

echo ""
echo "🧪 Testing model health..."

for model_info in "${models[@]}"; do
    IFS='|' read -r name role purpose vram <<< "$model_info"
    echo "   Testing $role ($name)..."
    if echo "Hello" | ollama run "$name" > /dev/null 2>&1; then
        echo "   ✅ $role responding"
    else
        echo "   ⚠️  $role test failed"
    fi
done

echo ""
echo "📊 VRAM Summary:"
echo "   Strategist: ~900MB"
echo "   Memory:     ~4.2GB"
echo "   Executor:   ~2.4GB"
echo "   Total:      ~7.5GB (within 8GB limit)"
echo ""

echo "✅ Ollama setup complete!"
echo ""
echo "Next steps:"
echo "   1. Verify models: ollama list"
echo "   2. Test health: python -m ai_factory.advisor.advisor_service"
echo "   3. Start Factory: python scripts/run_factory.py"
echo ""

