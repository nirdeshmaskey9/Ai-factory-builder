import os
import sys
import shutil
import subprocess
import httpx
from fastapi.testclient import TestClient
from ai_factory.main import app
from ai_factory.advisor.advisor_service import verify_local_health


def _run_script(path):
    env = os.environ.copy()
    env['DRY_RUN'] = '1'
    if path.endswith('.ps1'):
        shell = shutil.which('pwsh') or shutil.which('powershell')
        if not shell:
            import pytest
            pytest.skip('PowerShell not available')
        # Bypass policy for CI
        cmd = [shell, '-NoLogo']
        if 'powershell' in shell.lower():
            cmd += ['-ExecutionPolicy', 'Bypass']
        cmd += ['-File', path]
    else:
        shell = shutil.which('bash')
        if not shell:
            import pytest
            pytest.skip('bash not available')
        cmd = [shell, path]
    return subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def test_run_local_trio_scripts_dry_run():
    # Prefer native shell
    ps1 = os.path.join('scripts', 'run_local_trio.ps1')
    sh = os.path.join('scripts', 'run_local_trio.sh')
    if os.name == 'nt' and os.path.exists(ps1):
        r = _run_script(ps1)
        assert r.returncode == 0
    elif os.path.exists(sh):
        r = _run_script(sh)
        assert r.returncode == 0


def test_check_local_trio_scripts_dry_run():
    ps1 = os.path.join('scripts', 'check_local_trio.ps1')
    sh = os.path.join('scripts', 'check_local_trio.sh')
    # These scripts do not use DRY_RUN, but they only curl/Invoke URLs; allow run
    if os.name == 'nt' and os.path.exists(ps1):
        r = _run_script(ps1)
        assert r.returncode == 0 or r.returncode is None
    elif os.path.exists(sh):
        r = _run_script(sh)
        assert r.returncode == 0 or r.returncode is None


def test_advisor_startup_health_summary(monkeypatch):
    # Mock httpx get to make all three healthy
    real_get = httpx.Client.get
    def ok_get(self, url, *args, **kwargs):
        class R:
            status_code = 200
            def json(self):
                return {"version":"0.1"}
            text = 'ok'
        if '/api/version' in url:
            return R()
        return real_get(self, url, *args, **kwargs)
    monkeypatch.setattr(httpx.Client, 'get', ok_get)

    client = TestClient(app)
    info = client.get('/factory/info').json()
    h = info.get('local_trio_health') or {}
    assert h.get('strategist') is not False and h.get('memory') is not False and h.get('executor') is not False
    # Also verify via direct call
    res = verify_local_health({
        'strategist': os.getenv('AI_FACTORY_LOCAL_STRATEGIST_URL', 'http://127.0.0.1:11434'),
        'memory': os.getenv('AI_FACTORY_LOCAL_MEMORY_URL', 'http://127.0.0.1:11435'),
        'executor': os.getenv('AI_FACTORY_LOCAL_EXECUTION_URL', 'http://127.0.0.1:11436'),
    })
    assert all(res.values())

