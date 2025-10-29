$ports = @(11434, 11435, 11436)
Write-Host "Checking local trio health..."
foreach ($p in $ports) {
  try {
    $resp = Invoke-RestMethod -Uri "http://127.0.0.1:$p/api/version" -TimeoutSec 3
    Write-Host ("Port {0} OK ({1})" -f $p, $resp.version)
  } catch {
    Write-Host ("Port {0} not responding" -f $p)
  }
}
