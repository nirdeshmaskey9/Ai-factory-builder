"""
AI Factory Stress Tester
Runs controlled reliability and performance tests on the deployer/orchestrator system.
Ensures concurrency, endpoint health, and automatic cleanup of temporary apps.
"""
from __future__ import annotations

import asyncio
import time
import os
import signal
from pathlib import Path
from typing import List, Tuple, Dict, Any

import httpx

from ai_factory.deployer import deployer_agent, deployer_store


async def _verify(port: int, deployment_id: int) -> Tuple[bool, float, int]:
    """Ping the /hello endpoint and return (success, latency, id)."""
    url = f"http://127.0.0.1:{port}/hello"
    t0 = time.perf_counter()
    ok = False
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get(url)
            ok = (r.status_code == 200)
    except Exception:
        ok = False
    latency = round(time.perf_counter() - t0, 3)
    return (ok, latency, deployment_id)


async def _cleanup(deployment_ids: List[int]) -> List[int]:
    """Attempt to stop all given deployments. Returns list of stopped IDs."""
    stopped: List[int] = []
    for did in deployment_ids:
        # Prefer orchestrated rollback which is cross-platform
        try:
            deployer_agent.rollback(did)
            stopped.append(did)
            continue
        except Exception:
            pass
        # Fallback: try PID kill when available
        try:
            pid = deployer_store.get_pid(did)
            if pid:
                # Use SIGTERM if available; on Windows this acts like terminate
                os.kill(int(pid), signal.SIGTERM)
                stopped.append(did)
        except Exception:
            # best-effort cleanup
            pass
        # Small delay between terminations
        await asyncio.sleep(0.05)
    return stopped


async def run_stress_test(n: int = 5) -> Dict[str, Any]:
    """
    Launch n test deployments concurrently, verify /hello for each,
    and automatically stop them afterward.
    """
    start = time.time()
    ids: List[Tuple[int, int]] = []  # (deployment_id, port)
    print(f"🚀 Starting {n} concurrent deployments...")

    # Launch deployments (sequential dispatch with small stagger to avoid port races)
    for i in range(n):
        try:
            d = deployer_agent.deploy(goal=f"stress-test-{i}")
            dep_id = d.get("deployment_id") or d.get("id")
            port = d.get("port")
            if isinstance(dep_id, int) and isinstance(port, int):
                ids.append((dep_id, port))
        except Exception:
            pass
        await asyncio.sleep(0.3)

    # Verify concurrently
    tasks = [_verify(port, did) for (did, port) in ids]
    checks = await asyncio.gather(*tasks)

    ok_count = sum(1 for ok, _, _ in checks if ok)
    avg_latency = round(sum(lat for _, lat, _ in checks) / max(len(checks), 1), 3)
    elapsed = round(time.time() - start, 2)

    # Stop all stress-test deployments (best-effort)
    stopped = await _cleanup([did for (did, _) in ids])

    summary: Dict[str, Any] = {
        "total_runs": n,
        "successes": ok_count,
        "failures": max(n - ok_count, 0),
        "avg_latency_sec": avg_latency,
        "elapsed_sec": elapsed,
        "stopped": stopped,
    }

    log_dir = Path("deployments")
    log_dir.mkdir(exist_ok=True)
    try:
        with open(log_dir / "stress_test.log", "a", encoding="utf-8") as f:
            f.write(f"{time.ctime()} | {summary}\n")
    except Exception:
        # ignore logging failures
        pass

    try:
        print(f"✅ Stress test complete: {summary}")
    except Exception:
        print("Stress test complete.")
    return summary

