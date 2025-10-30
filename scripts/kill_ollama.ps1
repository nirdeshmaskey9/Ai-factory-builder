Write-Host "🔪 Checking for rogue Ollama instances..." -ForegroundColor Yellow

# Kill any running Ollama processes
Get-Process | Where-Object { $_.ProcessName -like "ollama*" } | ForEach-Object {
    try {
        Write-Host "Killing PID $($_.Id) - $($_.ProcessName)" -ForegroundColor Red
        Stop-Process -Id $_.Id -Force
    } catch {
        Write-Warning "Failed to stop $($_.ProcessName): $_"
    }
}

# Double-check port 11434
$portInUse = (Get-NetTCPConnection -LocalPort 11434 -ErrorAction SilentlyContinue)
if ($portInUse) {
    Write-Host "Port 11434 still in use by PID $($portInUse.OwningProcess). Killing..." -ForegroundColor Red
    Stop-Process -Id $portInUse.OwningProcess -Force -ErrorAction SilentlyContinue
} else {
    Write-Host "✅ Port 11434 is clear." -ForegroundColor Green
}

