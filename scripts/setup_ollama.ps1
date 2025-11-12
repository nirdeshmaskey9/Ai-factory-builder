# ===============================
# 🧠 Ollama Setup Script
# AI Factory Builder v3.7.0 - Hybrid Brain Upgrade
# Hardware: Alienware m18 R2 (8GB VRAM / 32GB RAM)
# ===============================

Write-Host "🧠 AI Factory Builder - Ollama Local Trio Setup" -ForegroundColor Cyan
Write-Host "Phase: v3.7.0-hybrid-brain-initialization" -ForegroundColor Yellow
Write-Host ""

# Check if Ollama is installed
$ollamaExists = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $ollamaExists) {
    Write-Host "❌ Ollama not found. Please install Ollama first:" -ForegroundColor Red
    Write-Host "   https://ollama.ai/download" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Ollama found: $((Get-Command ollama).Source)" -ForegroundColor Green
Write-Host ""

# Verify Ollama is running
Write-Host "🔍 Checking Ollama daemon..." -ForegroundColor Cyan
try {
    $version = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/version" -TimeoutSec 5
    Write-Host "✅ Ollama daemon running (version $($version.version))" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Ollama daemon not running. Starting..." -ForegroundColor Yellow
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Minimized
    Start-Sleep -Seconds 3
    $maxTries = 10
    $tries = 0
    while ($tries -lt $maxTries) {
        try {
            $version = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/version" -TimeoutSec 3
            Write-Host "✅ Ollama daemon started (version $($version.version))" -ForegroundColor Green
            break
        } catch {
            $tries++
            Start-Sleep -Seconds 1
        }
    }
    if ($tries -ge $maxTries) {
        Write-Host "❌ Failed to start Ollama daemon" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "📦 Pulling Local Trio models (optimized for 8GB VRAM)..." -ForegroundColor Cyan
Write-Host ""

# Local Trio v5 Models
$models = @(
    @{
        Name = "qwen2:1.5b-instruct-q4_K_M"
        Role = "Strategist"
        Purpose = "Optimized reasoning"
        VRAM = "~900MB"
    },
    @{
        Name = "mistral:7b-instruct-v0.3-q4_K_M"
        Role = "Memory"
        Purpose = "Contextual synthesis"
        VRAM = "~4.2GB"
    },
    @{
        Name = "phi3:mini-4k-instruct-q4_K_M"
        Role = "Executor"
        Purpose = "Code execution"
        VRAM = "~2.4GB"
    }
)

$totalVRAM = 0
foreach ($model in $models) {
    Write-Host "📥 Pulling $($model.Role) model: $($model.Name) ($($model.VRAM))..." -ForegroundColor Yellow
    $startTime = Get-Date
    
    try {
        $process = Start-Process -FilePath "ollama" -ArgumentList "pull", $model.Name -NoNewWindow -PassThru -Wait
        if ($process.ExitCode -eq 0) {
            $duration = (Get-Date) - $startTime
            Write-Host "   ✅ $($model.Role) model ready ($($duration.TotalSeconds.ToString('F1'))s)" -ForegroundColor Green
        } else {
            Write-Host "   ❌ Failed to pull $($model.Name)" -ForegroundColor Red
        }
    } catch {
        Write-Host "   ❌ Error: $_" -ForegroundColor Red
    }
    Write-Host ""
}

Write-Host "🔍 Verifying installed models..." -ForegroundColor Cyan
try {
    $list = ollama list
    Write-Host $list
} catch {
    Write-Host "⚠️  Could not list models" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🧪 Testing model health..." -ForegroundColor Cyan

foreach ($model in $models) {
    Write-Host "   Testing $($model.Role) ($($model.Name))..." -ForegroundColor Yellow
    try {
        $testPrompt = "Hello"
        $response = ollama run $model.Name $testPrompt 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ $($model.Role) responding" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  $($model.Role) test failed" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "   ⚠️  $($model.Role) test error: $_" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "📊 VRAM Summary:" -ForegroundColor Cyan
Write-Host "   Strategist: ~900MB" -ForegroundColor White
Write-Host "   Memory:     ~4.2GB" -ForegroundColor White
Write-Host "   Executor:   ~2.4GB" -ForegroundColor White
Write-Host "   Total:      ~7.5GB (within 8GB limit)" -ForegroundColor Green
Write-Host ""

Write-Host "✅ Ollama setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "   1. Verify models: ollama list" -ForegroundColor White
Write-Host "   2. Test health: python -m ai_factory.advisor.advisor_service" -ForegroundColor White
Write-Host "   3. Start Factory: python scripts/run_factory.py" -ForegroundColor White
Write-Host ""

