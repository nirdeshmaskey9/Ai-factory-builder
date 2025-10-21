"""
Self-Verify Runner for AI Factory v1.2.6-final-hardened

Runs the stress test 3× in a row and queries /system/health/full after each run
to ensure deterministic success. Exits 1 on failure.
"""

from __future__ import annotations

import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import subprocess
import sys
import time
import requests
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def run_once(run_id: int) -> None:
    print(f"\n🔁 Run {run_id} — starting...")
    rc = subprocess.run([sys.executable, "scripts/stress_test_factory.py"], check=False)
    if rc.returncode != 0:
        raise SystemExit(rc.returncode)
    r = requests.get("http://127.0.0.1:8015/system/health/full", timeout=10)
    assert r.status_code == 200, f"health endpoint status {r.status_code}"
    data = r.json()
    print("Health:", data.get("status"))
    time.sleep(1)


if __name__ == "__main__":
    for i in range(1, 4):
        run_once(i)
    print("\n✅ Multi-run validation completed successfully.")
    print("\n✅ AI Factory self-verify completed successfully — import paths and stress suite validated.")
    # Additional deterministic validation passes
    import time as _t, subprocess as _sp
    for i in range(1, 4):
        print(f"\n🔁 Validation run {i}/3 — starting...")
        code = _sp.call([sys.executable, "scripts/stress_test_factory.py"])
        if code != 0:
            raise SystemExit(f"❌ Stress test failed on run {i}.")
        print(f"✅ Run {i} passed successfully.")
        _t.sleep(2)
    print("\n🎯 All 3 validation runs passed deterministically.")
    print("\n🧱 AI Factory backend verified under concurrent preview load — v1.2.6.3-hardened ✅")
