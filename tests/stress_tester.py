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
from ai_factory.memory.memory_db import SessionLocal, SupervisorSession
import uuid


async def _wait_for_ready(port: int, started_at: float, timeout: float = 15.0) -> Tuple[bool, float]:
    """Poll /hello until it responds 200 or timeout. Returns (ok, ready_time_sec_from_start)."""
    url = f"http://127.0.0.1:{port}/hello"
    while True:
        try:
            async with httpx.AsyncClient(timeout=3) as c:
                r = await c.get(url)
                if r.status_code == 200:
                    return True, round(time.time() - started_at, 2)
        except Exception:
            pass
        if (time.time() - started_at) > timeout:
            return False, round(timeout, 2)
        await asyncio.sleep(1)


def _create_supervisor_session(goal: str) -> int:
    """Create a minimal SupervisorSession row so deploy() can resolve it."""
    req_id = str(uuid.uuid4())
    with SessionLocal() as session:
        row = SupervisorSession(
            request_id=req_id,
            goal=goal,
            plan="[stress] plan",
            context="[stress] context",
            result="[stress] result",
            status="ok",
        )
        session.add(row)
        session.commit()
        return int(row.id)


async def _deploy_one(i: int) -> Tuple[int, int, float] | Tuple[None, None, None]:
    """Create a session and deploy in a background thread. Returns (id, port, started_at)."""
    goal = f"stress-test-{i}"
    try:
        sess_id = _create_supervisor_session(goal)
        started_at = time.time()
        d = await asyncio.to_thread(deployer_agent.deploy, session_id=sess_id, goal=goal)
        # Prefer explicit session_id path if available
        if not d or not isinstance(d, dict):
            return (None, None, None)
        dep_id = d.get("deployment_id") or d.get("id")
        port = d.get("port")
        if isinstance(dep_id, int) and isinstance(port, int):
            return (dep_id, port, started_at)
    except Exception:
        return (None, None, None)
    return (None, None, None)


async def _cleanup(deployment_ids: List[int]) -> List[int]:
    """Attempt to stop all given deployments. Returns list of stopped IDs."""
    stopped: List[int] = []
    for did in deployment_ids:
        # Prefer orchestrated rollback which is cross-platform
        try:
            await asyncio.to_thread(deployer_agent.rollback, did)
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
    print(f"🚀 Launching {n} deployments (adaptive wait)...")

    # Launch deployments concurrently in background threads
    launch_tasks = [_deploy_one(i) for i in range(n)]
    launched = await asyncio.gather(*launch_tasks)
    runs = [
        {"deployment_id": did, "port": port, "started_at": started_at}
        for (did, port, started_at) in launched
        if isinstance(did, int) and isinstance(port, int) and isinstance(started_at, (int, float))
    ]
    if not runs:
        # Nothing launched; short-circuit with empty summary
        elapsed = round(time.time() - start, 2)
        summary = {
            "total_runs": n,
            "successes": 0,
            "failures": n,
            "avg_ready_time_sec": 0.0,
            "elapsed_sec": elapsed,
            "stopped": [],
        }
        log_dir = Path("deployments")
        log_dir.mkdir(exist_ok=True)
        try:
            with open(log_dir / "stress_test.log", "a", encoding="utf-8") as f:
                f.write(f"{time.ctime()} | {summary}\n")
        except Exception:
            pass
        try:
            print(f"✅ Stress test finished: {summary}")
        except Exception:
            print("Stress test complete.")
        return summary

    # Verify readiness concurrently with adaptive wait
    tasks = [_wait_for_ready(run["port"], run["started_at"]) for run in runs]
    checks = await asyncio.gather(*tasks)

    # Annotate runs with results and mark notes in store
    successes: List[float] = []
    for run, (ok, ready_time) in zip(runs, checks):
        run["ok"] = ok
        run["ready_time_sec"] = ready_time
        run["ready_at"] = time.time() if ok else None
        # Append verification note without changing status
        try:
            dep = deployer_store.get_deployment(run["deployment_id"])  # type: ignore
            if dep:
                cur_status = dep.status
                note = (
                    f"verified (ready_time={ready_time}s)"
                    if ok
                    else f"failed readiness (timeout={ready_time}s)"
                )
                deployer_store.update_status(run["deployment_id"], cur_status, notes=note)  # type: ignore
        except Exception:
            pass
        if ok:
            successes.append(float(ready_time))

    ok_count = sum(1 for r in runs if r.get("ok"))
    avg_ready = round(sum(successes) / max(len(successes), 1), 2) if successes else 0.0
    elapsed = round(time.time() - start, 2)

    # Stop all stress-test deployments (best-effort)
    stopped = await _cleanup([int(r["deployment_id"]) for r in runs])

    summary: Dict[str, Any] = {
        "total_runs": n,
        "successes": ok_count,
        "failures": max(n - ok_count, 0),
        "avg_ready_time_sec": avg_ready,
        "elapsed_sec": elapsed,
        "stopped": stopped,
    }

    log_dir = Path("deployments")
    log_dir.mkdir(exist_ok=True)
    try:
        with open(log_dir / "stress_test.log", "a", encoding="utf-8") as f:
            f.write(f"{time.ctime()} | {summary} | runs={runs}\n")
    except Exception:
        # ignore logging failures
        pass

    try:
        print(f"✅ Stress test finished: {summary}")
    except Exception:
        print("Stress test complete.")
    return summary



