param(
  [int]$n = 10
)

Write-Host "🧠 Starting load_sim.ps1..."

try {
  for ($i=0; $i -lt $n; $i++) {
    Invoke-RestMethod -Uri "http://127.0.0.1:8015/factory/create" `
      -Method POST `
      -Body '{"goal":"Create a FastAPI app with /hello and /health","domain":"web","dynamic":true}' `
      -ContentType "application/json" | Out-Null
  }

  Invoke-RestMethod -Uri "http://127.0.0.1:8015/deployer/preview/stop_all" -Method GET | Out-Null
  Write-Host "Burst load ($n) completed."
} catch {
  Write-Host "❌ load_sim.ps1 error: $($_.Exception.Message)"
} finally {
  Write-Host "✅ load_sim.ps1 completed successfully."
}
