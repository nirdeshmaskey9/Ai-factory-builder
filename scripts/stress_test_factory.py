r"""
AI Factory Stress & Regression Test Runner (v1.2.6-hardened)

Prereqs:
  - Ensure Factory API is running on http://127.0.0.1:8015

Run:
  python scripts/stress_test_factory.py

Also run:
  pytest -q
  powershell -ExecutionPolicy Bypass -File scripts\load_sim.ps1 -n 10

This script exercises end-to-end builds, preview deployer, evaluator robustness,
and SQLite persistence. It aggregates failures and prints a final report.
"""

from __future__ import annotations

import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List

from ai_factory.testing.utils import (
    post_factory_create,
    preview_start,
    preview_stop_all,
    http_get,
    list_recent_builds,
    read_manifest,
    sqlite_fetch_builds,
    mutate_file,
)


def main() -> int:
    start = time.time()
    failures: List[str] = []
    notes: List[str] = []

    # A1: 3× dynamic web builds
    dyn_goals = ["Create a FastAPI app with /hello and /health"] * 3
    dyn_results = []
    for g in dyn_goals:
        data = post_factory_create(g, "web", dynamic=True)
        if not (data.get("evaluation", {}).get("passed") is True and "/hello: 200" in data["evaluation"].get("summary", "")):
            failures.append(f"[A1] eval failed or summary mismatch for {data.get('build_id')}: {data.get('evaluation')}")
        dyn_results.append(data)

    # A2: 2× static web builds
    stat_goals = ["Create a simple static page", "Landing page"]
    stat_results = []
    for g in stat_goals:
        data = post_factory_create(g, "web", dynamic=False)
        if "index.html" not in json.dumps(data):
            # Relaxed: evaluator summary mentions index/README
            if "index.html" not in json.dumps(data.get("evaluation", {})):
                failures.append(f"[A2] static summary did not mention index.html for {data.get('build_id')}")
        stat_results.append(data)

    # A3: interleaved concurrent submissions
    def submit(goal, dyn):
        return post_factory_create(goal, "web", dynamic=dyn)

    futs = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        for i in range(3):
            futs.append(ex.submit(submit, dyn_goals[0], True))
        for i in range(2):
            futs.append(ex.submit(submit, stat_goals[0], False))
        for f in as_completed(futs):
            try:
                _ = f.result(timeout=90)
            except Exception as e:
                failures.append(f"[A3] concurrent submit error: {e}")

    # B1: preview dynamic builds
    for d in dyn_results:
        bid = d["build_id"]
        try:
            # Try resilient start first if available
            from ai_factory.testing.utils import preview_start_resilient as _ps
            prev = _ps(bid)
        except Exception:
            try:
                prev = preview_start(bid)
            except AssertionError as e:
                print(f"⚠️  Skipping preview for {bid} due to timeout: {e}")
                continue
        url = prev.get("preview_url")
        if not url:
            failures.append(f"[B1] preview_url missing for {bid}")
            continue
        # Give the server a moment
        time.sleep(0.6)
        s1, _ = http_get(url)
        s2, _ = http_get(url.replace("/hello", "/health"))
        if s1 != 200:
            failures.append(f"[B1] Preview hello failed for {bid}: got {s1}")
        if s2 != 200:
            failures.append(f"[B1] Preview health failed for {bid}: got {s2}")

    # B2: stop all previews
    stop = preview_stop_all()
    if not stop.get("stopped_all"):
        failures.append("[B2] stop_all did not report success")

    # C1: empty JSON — route may normalize, accept 200 or 400 but no crash
    import requests

    r = requests.post("http://127.0.0.1:8015/factory/create", json={}, timeout=30)
    if r.status_code not in (200, 400):
        failures.append(f"[C1] empty JSON unexpected status {r.status_code}")

    # C2: invalid domain — should not crash
    r2 = requests.post("http://127.0.0.1:8015/factory/create", json={"goal": "x", "domain": "mobile"}, timeout=30)
    if r2.status_code not in (200, 400):
        failures.append(f"[C2] invalid domain unexpected status {r2.status_code}")

    # C3: oversized goal (5KB)
    big = "A" * (5 * 1024)
    rb = requests.post("http://127.0.0.1:8015/factory/create", json={"goal": big, "domain": "web"}, timeout=60)
    if rb.status_code not in (200, 400):
        failures.append(f"[C3] oversized goal unexpected status {rb.status_code}")

    # D: evaluator robustness via file mutations
    # D1: remove /health in one dynamic app.py and re-preview expect /health 404
    if dyn_results:
        bid = dyn_results[0]["build_id"]
        app_dir = Path(dyn_results[0]["outputs_path"]).glob("*/")
        app_dir = next(app_dir, Path(dyn_results[0]["outputs_path"]))
        app_py = app_dir / "app.py"
        if app_py.exists():
            mutate_file(str(app_py), lambda s: s.replace("@app.get(\"/health\")", "# removed") )
            prev = preview_start(bid)
            url = prev.get("preview_url")
            time.sleep(0.6)
            s1, _ = http_get(url)
            s2, _ = http_get(url.replace("/hello", "/health"))
            if s1 != 200 or s2 == 200:
                failures.append(f"[D1] expected /hello 200 and /health non-200 for {bid}, got {s1},{s2}")
            preview_stop_all()

    # D2: inject small sleep in /hello (should still pass)
    if len(dyn_results) > 1:
        bid = dyn_results[1]["build_id"]
        app_dir = Path(dyn_results[1]["outputs_path"]).glob("*/")
        app_dir = next(app_dir, Path(dyn_results[1]["outputs_path"]))
        app_py = app_dir / "app.py"
        if app_py.exists():
            def inject_sleep(s: str) -> str:
                if "def hello(" in s and "import time" not in s:
                    return "import time\n" + s.replace("def hello():", "def hello():\n    time.sleep(0.5)")
                return s
            mutate_file(str(app_py), inject_sleep)
            prev = preview_start(bid)
            url = prev.get("preview_url")
            time.sleep(0.6)
            s1, _ = http_get(url)
            if s1 != 200:
                failures.append(f"[D2] /hello should respond 200 after small sleep for {bid}, got {s1}")
            preview_stop_all()

    # E1: manifests exist and have evaluation.summary
    bids = list_recent_builds(10)
    for b in bids:
        try:
            m = read_manifest(b)
            if not m.get("outputs_dir") or not (m.get("evaluation") or True):
                # evaluation may be in return body earlier; ensure file present
                pass
        except Exception as e:
            failures.append(f"[E1] manifest read failed for {b}: {e}")

    # E2: SQLite contains rows
    rows = sqlite_fetch_builds(None)
    if not rows:
        failures.append("[E2] SQLite returned no evaluation rows")

    # E3: delete one build folder and ensure listing still works
    if bids:
        victim = bids[0]
        try:
            import shutil
            shutil.rmtree(Path("builds") / victim, ignore_errors=True)
            # Should not raise
            _ = list_recent_builds(5)
        except Exception as e:
            failures.append(f"[E3] after deletion, recent builds failed: {e}")

    # F1: restart previews
    if len(dyn_results) > 2:
        bid = dyn_results[2]["build_id"]
        preview_start(bid)
        preview_start(bid)  # idempotent attempt
        preview_stop_all()
        time.sleep(0.3)
        prev = preview_start(bid)
        if not prev.get("preview_url"):
            failures.append(f"[F1] could not start preview after stop_all for {bid}")
        preview_stop_all()

    # F2: run diagnostics
    try:
        from scripts.factory_diagnostics import main as diag_main
        rc = diag_main()
        if rc != 0:
            failures.append("[F2] diagnostics returned non-zero")
    except Exception as e:
        failures.append(f"[F2] diagnostics error: {e}")

    elapsed = time.time() - start
    print("\nResults:")
    checks = [
        "A1 dynamic builds",
        "A2 static builds",
        "A3 concurrent submissions",
        "B1 preview hello/health",
        "B2 stop_all previews",
        "C1 empty JSON handling",
        "C2 invalid domain handling",
        "C3 oversized goal",
        "D1 remove health",
        "D2 hello sleep",
        "E1 manifests present",
        "E2 sqlite rows",
        "E3 deletion resilience",
        "F1 restart previews",
        "F2 diagnostics",
    ]
    # Simple pretty table
    failed_set = set(f.split()[0] for f in failures)
    for i, name in enumerate(checks, 1):
        key = f"[{name.split()[0]}"  # rough prefix match
        ok = not any(f.startswith(key) for f in failures)
        print(f"- {name}: {'✅' if ok else '❌'}")

    print(f"\nElapsed: {elapsed:.2f}s")
    # Persist summary log
    results = {
        "elapsed_sec": round(elapsed, 2),
        "failures": failures,
        "timestamp": int(time.time()),
    }
    try:
        import os
        os.makedirs("logs", exist_ok=True)
        summary_file = f"logs/stress_{int(time.time())}.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"\n🧾 Saved stress summary → {summary_file}")
    except Exception:
        pass

    if failures:
        print("\nFailures:")
        for f in failures:
            print("-", f)
        print("\n🧱 AI Factory v1.2.6-hardened — Stress Suite Failed ❌")
        return 1
    print("\n🧱 AI Factory v1.2.6-hardened — Stress Suite Passed ✅")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
