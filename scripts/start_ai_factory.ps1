<#[
 =========================================================
 🧠 AI Factory Auto-Launcher v3.2.5 - Unified Trio Edition
 Starts Ollama + AI Factory, waits for readiness, verifies
 health, and gracefully shuts down both on exit.
 =========================================================
]#>

Write-Host "🧠 Starting start_ai_factory.ps1..."

# --- CONFIG ---
$projectPath = "C:\projects\ai_factory_builder"
$venvPath = "$projectPath\.venv\Scripts\Activate.ps1"
$uvicornApp = "ai_factory.main:app"
$ollamaPort = 11434
$healthUrl = "http://127.0.0.1:8000/advisor/trio_health"

# --- STEP 1: Kill any previous Ollama instances ---
Write-Host "🚿 Killing old Ollama instances..."
Get-Process ollama -ErrorAction SilentlyContinue | Stop-Process -Force

# --- STEP 2: Start Ollama as a background process ---
Write-Host "🚀 Starting Ollama daemon..."
$ollama = Start-Process -FilePath "ollama.exe" -ArgumentList "serve" -WindowStyle Minimized -PassThru
Start-Sleep -Seconds 5

# --- STEP 3: Wait for Ollama to be ready ---
$maxTries = 20; $tries = 0
while ($tries -lt $maxTries) {
    try {
        $resp = Invoke-RestMethod -Uri "http://127.0.0.1:$ollamaPort/api/version" -TimeoutSec 3
        if ($resp.version) {
            Write-Host "✅ Ollama ready (version $($resp.version))"
            break
        }
    } catch {}
    Start-Sleep -Seconds 2; $tries++
}
if ($tries -ge $maxTries) { Write-Host "⚠️ Ollama failed to start."; exit 1 }

# --- STEP 4: Start AI Factory ---
Write-Host "⚙️ Starting AI Factory (Uvicorn)..."
$factoryProc = Start-Process -FilePath "pwsh" -ArgumentList "-NoExit", "-Command", "cd $projectPath; & $venvPath; uvicorn $uvicornApp --reload" -WindowStyle Minimized -PassThru
Start-Sleep -Seconds 8

# --- STEP 5: Health check ---
Write-Host "🔎 Checking trio health..."
try {
    $health = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 5
    if ($health.roles.strategist.healthy -and $health.roles.memory.healthy -and $health.roles.executor.healthy) {
        Write-Host "✅ All trio roles healthy - AI Factory online!"
    } else {
        Write-Host "⚠️ Partial health:" ($health | ConvertTo-Json -Depth 3)
    }
} catch {
    Write-Host "⚠️ Health check failed - verify AI Factory on port 8000."
}

# --- STEP 6: Graceful shutdown handler ---
Register-EngineEvent PowerShell.Exiting -Action {
    Write-Host "`n🛑 Shutting down AI Factory + Ollama..."
    try {
        if ($factoryProc -and !$factoryProc.HasExited) { $factoryProc.CloseMainWindow(); Start-Sleep 2; $factoryProc.Kill() }
        if ($ollama -and !$ollama.HasExited) { $ollama.CloseMainWindow(); Start-Sleep 2; $ollama.Kill() }
    } catch {}
    Write-Host "✅ Shutdown complete."
} | Out-Null

Write-Host "✅ Startup complete - both services running. Press Ctrl+C or close window to exit."
Wait-Event  # Keeps script alive until you close it

Write-Host "✅ start_ai_factory.ps1 completed successfully."

