# ===============================
# 🧪 Local Trio Validation Script
# AI Factory Builder v3.7.0
# ===============================

Write-Host "🧪 Validating Local Trio Configuration" -ForegroundColor Cyan
Write-Host ""

$OLLAMA_HOST = $env:OLLAMA_HOST
if (-not $OLLAMA_HOST) {
    $OLLAMA_HOST = "http://127.0.0.1:11434"
}

$models = @(
    @{ Role = "Strategist"; Model = "qwen2:1.5b-instruct-q4_K_M"; ExpectedVRAM = 900 },
    @{ Role = "Memory"; Model = "mistral:7b-instruct-v0.3-q4_K_M"; ExpectedVRAM = 4200 },
    @{ Role = "Executor"; Model = "phi3:mini"; ExpectedVRAM = 2400 }
)

Write-Host "🔍 Checking Ollama connectivity..." -ForegroundColor Yellow
try {
    $version = Invoke-RestMethod -Uri "$OLLAMA_HOST/api/version" -TimeoutSec 5
    Write-Host "✅ Ollama daemon reachable (version $($version.version))" -ForegroundColor Green
} catch {
    Write-Host "❌ Ollama daemon not reachable at $OLLAMA_HOST" -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "📋 Checking installed models..." -ForegroundColor Yellow
$installed = ollama list 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host $installed
} else {
    Write-Host "⚠️  Could not list models" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🧪 Testing model inference..." -ForegroundColor Yellow
$results = @()

foreach ($m in $models) {
    Write-Host "   Testing $($m.Role) ($($m.Model))..." -ForegroundColor Cyan
    $startTime = Get-Date
    
    try {
        $testPrompt = "Say hello in one word."
        $response = ollama run $m.Model $testPrompt 2>&1 | Out-String
        
        $endTime = Get-Date
        $latency = ($endTime - $startTime).TotalMilliseconds
        
        if ($LASTEXITCODE -eq 0 -and $response -match "hello|hi|hey") {
            Write-Host "      ✅ $($m.Role) responding (${latency}ms)" -ForegroundColor Green
            $results += @{
                Role = $m.Role
                Model = $m.Model
                Status = "Healthy"
                Latency = $latency
            }
        } else {
            Write-Host "      ⚠️  $($m.Role) responded but may have issues" -ForegroundColor Yellow
            $results += @{
                Role = $m.Role
                Model = $m.Model
                Status = "Warning"
                Latency = $latency
            }
        }
    } catch {
        Write-Host "      ❌ $($m.Role) failed: $_" -ForegroundColor Red
        $results += @{
            Role = $m.Role
            Model = $m.Model
            Status = "Failed"
            Latency = 0
        }
    }
}

Write-Host ""
Write-Host "📊 Validation Summary:" -ForegroundColor Cyan
Write-Host "====================" -ForegroundColor Cyan
foreach ($r in $results) {
    $statusColor = switch ($r.Status) {
        "Healthy" { "Green" }
        "Warning" { "Yellow" }
        default { "Red" }
    }
    Write-Host "  $($r.Role): $($r.Status) ($($r.Latency.ToString('F0'))ms)" -ForegroundColor $statusColor
}

$healthyCount = ($results | Where-Object { $_.Status -eq "Healthy" }).Count
Write-Host ""
if ($healthyCount -eq 3) {
    Write-Host "✅ All models healthy and ready!" -ForegroundColor Green
} elseif ($healthyCount -gt 0) {
    Write-Host "⚠️  Some models need attention ($healthyCount/3 healthy)" -ForegroundColor Yellow
} else {
    Write-Host "❌ No models responding. Check Ollama installation." -ForegroundColor Red
}

Write-Host ""
Write-Host "💾 VRAM Estimate: ~7.5GB total (within 8GB limit)" -ForegroundColor Cyan
Write-Host ""

