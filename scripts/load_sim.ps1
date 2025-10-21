param(
  [int]$n = 10
)

for ($i=0; $i -lt $n; $i++) {
  Invoke-RestMethod -Uri "http://127.0.0.1:8015/factory/create" `
    -Method POST `
    -Body '{"goal":"Create a FastAPI app with /hello and /health","domain":"web","dynamic":true}' `
    -ContentType "application/json" | Out-Null
}

Invoke-RestMethod -Uri "http://127.0.0.1:8015/deployer/preview/stop_all" -Method GET | Out-Null
Write-Host "Burst load ($n) completed."

