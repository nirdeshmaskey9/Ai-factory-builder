param()
$ErrorActionPreference = 'Stop'

Write-Host "🧠 Starting demo_memory_phase3.ps1..."

try {
    Write-Host "Starting server (background)"
    $p = Start-Process -PassThru -NoNewWindow -FilePath python -ArgumentList '-m','uvicorn','ai_factory.main:app','--reload'
    Start-Sleep -Seconds 2

    Write-Host "Create a couple orchestrator-like runs (via planner)"
    Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/planner/dispatch -ContentType 'application/json' -Body '{"prompt":"Build a FastAPI app","task_type":"coding"}' | Out-Null
    Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/planner/dispatch -ContentType 'application/json' -Body '{"prompt":"Create a CLI tool","task_type":"coding"}' | Out-Null

    Write-Host "Trigger learning"
    $learn = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/memory/learn -ContentType 'application/json' -Body '{}'
    $learn | ConvertTo-Json

    Write-Host "Open dashboard: /dashboard/memory?q=fastapi"
    Write-Host "Visit: http://127.0.0.1:8000/dashboard/memory?q=fastapi"

    Write-Host "Stats:"
    $stats = Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8000/memory/stats
    $stats | ConvertTo-Json
} catch {
    Write-Host "❌ demo_memory_phase3.ps1 error: $($_.Exception.Message)"
} finally {
    if ($p -and $p.Id) { Stop-Process -Id $p.Id -ErrorAction SilentlyContinue }
    Write-Host "✅ demo_memory_phase3.ps1 completed successfully."
}
