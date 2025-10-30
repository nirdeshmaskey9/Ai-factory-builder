<#
 ================================
 💤 JoJo Pause Script — v3.2.6-TCE
 ================================
#>
param()

$ErrorActionPreference = 'Stop'

Write-Host "🧠 Starting pause_jojo.ps1..."
Write-Host "🌙 Pausing JoJo safely..."
Set-Location "C:\projects\ai_factory_builder"

# Optional dry-run mode: set JOJO_DRY_RUN=1 to skip side effects
$isDry = ($env:JOJO_DRY_RUN -eq '1' -or $env:DRY_RUN -eq '1')
if ($isDry) { Write-Host "(dry-run) Side effects disabled." }

try {
    # Stop all processes
    $processes = @("ollama", "python")
    foreach ($p in $processes) {
        try {
            $procs = Get-Process -Name $p -ErrorAction SilentlyContinue
            if ($procs) {
                if (-not $isDry) {
                    $procs | Stop-Process -Force -ErrorAction SilentlyContinue
                    Write-Host "🛑 Stopped $p."
                } else {
                    Write-Host "(dry-run) Would stop process: $p"
                }
            } else {
                Write-Host "ℹ️  $p not running."
            }
        } catch {
            Write-Host "⚠️  Error stopping $($p): $($_.Exception.Message)"
        }
    }

    # Snapshot
    Write-Host "💾 Saving snapshot..."
    try {
        if (-not $isDry) {
            git add . | Out-Null
            $status = git status --porcelain
            if (-not [string]::IsNullOrWhiteSpace($status)) {
                git commit -m "💤 Auto-snapshot before pause" | Out-Null
                try { git push | Out-Null } catch { Write-Host "⚠️  Push failed or no remote configured." }
                Write-Host "✅ Snapshot complete. JoJo safely paused."
            } else {
                Write-Host "ℹ️  No changes to commit. Snapshot skipped."
            }
        } else {
            Write-Host "(dry-run) Would run: git add .; git commit -m '💤 Auto-snapshot before pause'; git push"
            Write-Host "✅ (dry-run) Snapshot simulated."
        }
    } catch {
        Write-Host "⚠️  Git snapshot encountered an issue: $($_.Exception.Message)"
    }
} catch {
    Write-Host "❌ Error in pause_jojo.ps1: $($_.Exception.Message)"
} finally {
    Write-Host "✅ pause_jojo.ps1 completed successfully."
}

