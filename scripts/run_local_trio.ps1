param()

Write-Host "🧠 Starting run_local_trio.ps1..."
Write-Host "Launching local AI trio..."

$ports = @(11434, 11435, 11436)
$models = @("llama3.1:8b", "phi3:mini", "qwen2.5:1.5b")
$roles = @("Strategist", "Memory", "Executor")

for ($i = 0; $i -lt $ports.Length; $i++) {
    $env:OLLAMA_HOST = "127.0.0.1:$($ports[$i])"
    Start-Process -NoNewWindow ollama -ArgumentList "run", $models[$i]
    Write-Host "Starting $($roles[$i]) on port $($ports[$i])..."
}

Start-Sleep -Seconds 5

foreach ($p in $ports) {
    try {
        $resp = Invoke-RestMethod -Uri "http://127.0.0.1:$p/api/version" -TimeoutSec 3
        Write-Host ("Port {0} healthy ({1})" -f $p, $resp.version)
    } catch {
        Write-Host ("Port {0} unreachable" -f $p)
    }
}

Write-Host "Local trio check complete."
Write-Host "✅ run_local_trio.ps1 completed successfully."

