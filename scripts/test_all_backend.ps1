Write-Host "🧠 Running JoJo Backend Capability & Conversational Validation Suite..."

# Ensure clean environment
& "$PSScriptRoot\reset_bridge.ps1"

# Start JoJo backend
& "$PSScriptRoot\resume_jojo.ps1"
Start-Sleep -Seconds 10

# Run full capability test set
pytest -q tests/test_capability_suite.py
if ($LASTEXITCODE -ne 0) { Write-Error "❌ Capability Suite failed."; exit 1 }

# Run conversational realism chain
pytest -q tests/test_conversational_chain.py
if ($LASTEXITCODE -ne 0) { Write-Error "❌ Conversational Chain failed."; exit 1 }

# Run factory info verification
pytest -q tests/test_factory_info.py
if ($LASTEXITCODE -ne 0) { Write-Error "❌ Factory info test failed."; exit 1 }

# If all pass
Write-Host "✅ All backend intelligence tests passed — JoJo’s mind is stable and coherent."
& "$PSScriptRoot\pause_jojo.ps1"

