<#
 ================================
 🧠 JoJo Resume Script — v3.2.6-TCE
 ================================
#>
param()

$ErrorActionPreference = 'Stop'

Write-Host "🌅 Resuming JoJo..."
Set-Location "C:\projects\ai_factory_builder"

# Optional dry-run mode: set JOJO_DRY_RUN=1 to skip side effects
$isDry = ($env:JOJO_DRY_RUN -eq '1' -or $env:DRY_RUN -eq '1')
if ($isDry) { Write-Host "(dry-run) Side effects disabled." }

# Activate environment if available
$activatePath = Join-Path (Get-Location) ".venv\Scripts\Activate.ps1"
if (Test-Path $activatePath) {
    if (-not $isDry) {
        & $activatePath
    }
    else {
        Write-Host "(dry-run) Would activate venv: $activatePath"
    }
} else {
    Write-Host "⚠️  Python venv not found at .venv — continuing without activation."
}

# Start Ollama daemon (safe auto-launch)
try {
    $ollamaProc = Get-Process ollama -ErrorAction SilentlyContinue
    if (-not $ollamaProc) {
        $ollamaExists = Get-Command ollama -ErrorAction SilentlyContinue
        if ($ollamaExists) {
            Write-Host "🚀 Starting Ollama..."
            if (-not $isDry) {
                Start-Process "ollama" -ArgumentList "serve" | Out-Null
                Start-Sleep -Seconds 5
            } else {
                Write-Host "(dry-run) Would run: ollama serve"
            }
        } else {
            Write-Host "⚠️  Ollama not found in PATH. Please install from https://ollama.ai and ensure it's available."
        }
    } else {
        Write-Host "✅ Ollama already running."
    }
} catch {
    Write-Host "⚠️  Could not start or detect Ollama: $($_.Exception.Message)"
}

# Start AI Factory backend
Write-Host "⚙️ Launching AI Factory..."
if (-not $isDry) {
    pwsh -File .\scripts\start_ai_factory.ps1
} else {
    Write-Host "(dry-run) Would launch: pwsh -File .\scripts\start_ai_factory.ps1"
}

# Verify health
Write-Host "🔍 Checking health..."
if (-not $isDry) {
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/factory/info" -TimeoutSec 10
        if ($null -ne $response) {
            $ver = $response.version
            if (-not $ver) { $ver = "unknown" }
            Write-Host "✅ JoJo Online — Version: $ver"
        } else {
            Write-Host "⚠️  Health endpoint returned no data."
        }
    } catch {
        Write-Host "⚠️  Could not verify Factory health — check manually if needed."
    }
} else {
    Write-Host "(dry-run) Would check: GET http://127.0.0.1:8000/factory/info"
}

