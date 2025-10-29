import subprocess
import shutil


def test_powershell_scripts():
    shell = shutil.which('powershell') or shutil.which('pwsh')
    if not shell:
        import pytest
        pytest.skip('PowerShell not available')
    r = subprocess.run(
        [shell, '-ExecutionPolicy', 'Bypass', '-File', 'scripts/check_local_trio.ps1'],
        capture_output=True, text=True
    )
    assert 'Port' in (r.stdout or '')
    assert r.returncode == 0

