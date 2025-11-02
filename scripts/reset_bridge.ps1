Write-Host "🧹 Resetting Bridge Environment..."
try {
    Get-Process python, uvicorn, ollama -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
} catch {}
try {
    Get-ChildItem "$PSScriptRoot\..\__pycache__" -Recurse -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
} catch {}
try {
    if (Test-Path ".pytest_cache") { Remove-Item ".pytest_cache" -Recurse -Force -ErrorAction SilentlyContinue }
} catch {}
try {
    netstat -ano | findstr 11434 | ForEach-Object {
        $pid = ($_ -split '\s+')[-1]
        if ($pid -match '^\d+$') { taskkill /PID $pid /F | Out-Null }
    }
} catch {}
Write-Host "✅ Bridge reset complete — ready for next run."

