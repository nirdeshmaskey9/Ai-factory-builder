<#
 ================================
 🧩 Script Validator & Integrity Anchor — v3.3.1
 Validates PowerShell scripts' syntax across the repo (excluding .venv/builds).
 Prints a clear summary and returns non-zero on failure.
 Usage:
   pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/validate_scripts.ps1
#>
param()

$ErrorActionPreference = 'Stop'

Write-Host "🔎 Validating PowerShell scripts..."

# Resolve repo root from scripts/ folder
$root = Resolve-Path (Join-Path $PSScriptRoot '..') | Select-Object -ExpandProperty Path

# Collect .ps1 files (exclude common transient dirs)
$files = Get-ChildItem -Path $root -Recurse -Filter '*.ps1' -File |
    Where-Object {
        $_.FullName -notmatch "\\\.venv\\" -and
        $_.FullName -notmatch "\\builds\\" -and
        $_.FullName -notmatch "\\.git\\" -and
        $_.FullName -notmatch "\\node_modules\\"
    } |
    Sort-Object FullName

if (-not $files) {
    Write-Host "ℹ️  No PowerShell scripts found to validate."
    exit 0
}

$failures = @()
$checked = 0

foreach ($f in $files) {
    $checked += 1
    try {
        $tokens = $null
        $errors = $null
        [void][System.Management.Automation.Language.Parser]::ParseFile($f.FullName, [ref]$tokens, [ref]$errors)
        if ($errors -and $errors.Count -gt 0) {
            $first = $errors | Select-Object -First 1
            Write-Host ("❌ {0}:{1} {2}" -f $f.FullName, $first.Extent.StartLineNumber, $first.Message)
            $failures += ,@($f.FullName, $first.Extent.StartLineNumber, $first.Message)
        } else {
            Write-Host ("✅ {0}" -f $f.FullName)
        }
    } catch {
        Write-Host ("❌ {0} {1}" -f $f.FullName, $_.Exception.Message)
        $failures += ,@($f.FullName, 0, $_.Exception.Message)
    }
}

Write-Host ("—" * 50)
Write-Host ("Checked scripts: {0}" -f $checked)
if ($failures.Count -gt 0) {
    Write-Host ("Failed scripts: {0}" -f ($failures.Count / 3))
    exit 1
} else {
    Write-Host "All scripts are valid. Safe to proceed."
}

exit 0

