from __future__ import annotations

import asyncio
import json
import os
import subprocess
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx


HOST = os.getenv("AI_FACTORY_HOST", "127.0.0.1")
PORT = int(os.getenv("AI_FACTORY_PORT", "8015"))
BASE = f"http://{HOST}:{PORT}"


@dataclass
class RouteCheck:
    name: str
    method: str
    path: str
    ok: bool
    status: Optional[int] = None
    error: Optional[str] = None
    latency_ms: Optional[int] = None


async def probe_routes() -> Tuple[List[RouteCheck], List[str]]:
    checks: List[RouteCheck] = []
    warnings: List[str] = []
    async with httpx.AsyncClient(timeout=5) as c:
        targets = [
            ("GET", "/orchestrator/status"),
            ("GET", "/deployer/list"),
            ("GET", "/memory/search?q=test&n=1"),
            ("POST", "/evaluator/learn"),
        ]
        for method, path in targets:
            url = BASE + path
            t0 = time.perf_counter()
            try:
                if method == "GET":
                    r = await c.get(url)
                else:
                    r = await c.post(url, json={"feedback": "audit-ping"})
                ok = 200 <= r.status_code < 300 or (path.endswith("/learn") and r.status_code in (200, 400))
                checks.append(RouteCheck(path, method, path, ok, r.status_code, None, int((time.perf_counter()-t0)*1000)))
                if not ok:
                    warnings.append(f"Route {method} {path} returned {r.status_code}")
            except Exception as e:
                checks.append(RouteCheck(path, method, path, False, None, str(e), None))
                warnings.append(f"Route {method} {path} error: {e}")
    return checks, warnings


def list_deploy_dirs() -> List[str]:
    d = Path("deployments")
    if not d.exists():
        return []
    out: List[str] = []
    for p in sorted(d.iterdir()):
        if p.is_dir() and p.name.isdigit():
            out.append(p.name)
    return out


async def fetch_deployments() -> Tuple[List[Dict[str, Any]], List[str]]:
    warnings: List[str] = []
    rows: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=5) as c:
        try:
            r = await c.get(BASE + "/deployer/list")
            if r.status_code == 200:
                data = r.json()
                items = data if isinstance(data, list) else []
                rows.extend(items)
            else:
                warnings.append(f"/deployer/list returned {r.status_code}")
        except Exception as e:
            warnings.append(f"/deployer/list error: {e}")
    return rows, warnings


async def check_running_endpoints(deploys: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    warnings: List[str] = []
    details: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=5) as c:
        tasks = []
        for d in deploys:
            if str(d.get("status")).lower() == "running" and d.get("port"):
                tasks.append((d, c.get(f"http://127.0.0.1:{int(d['port'])}/hello")))
        results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)
        for (d, _), res in zip(tasks, results):
            rec = {"id": d.get("id"), "port": d.get("port"), "status": d.get("status"), "ok": False}
            if isinstance(res, Exception):
                rec["error"] = str(res)
                warnings.append(f"Deploy {d.get('id')} error: {res}")
            else:
                rec["code"] = res.status_code
                try:
                    rec["body"] = res.json()
                except Exception:
                    rec["body"] = res.text
                rec["ok"] = res.status_code == 200
                if not rec["ok"]:
                    warnings.append(f"Deploy {d.get('id')} /hello returned {res.status_code}")
            details.append(rec)
    return details, warnings


def db_integrity() -> Tuple[bool, Optional[str]]:
    try:
        from ai_factory.memory.memory_db import SessionLocal
        from sqlalchemy import text
        with SessionLocal() as session:
            session.execute(text("select 1"))
            session.commit()
        return True, None
    except Exception as e:
        return False, str(e)


def essential_files() -> Tuple[List[str], List[str]]:
    missing: List[str] = []
    present: List[str] = []
    paths = [
        "ai_factory/services/deployer_service.py",
        "ai_factory/services/orchestrator_service.py",
        "ai_factory/orchestrator/orchestrator_router.py",
        "ai_factory/deployer/deployer_router.py",
    ]
    for p in paths:
        if Path(p).exists():
            present.append(p)
        else:
            missing.append(p)
    return present, missing


def env_checks() -> Tuple[List[str], List[str]]:
    ok: List[str] = []
    warn: List[str] = []
    key = os.getenv("OPENAI_API_KEY")
    if key and len(key) >= 10:
        ok.append("OPENAI_API_KEY present")
    else:
        warn.append("OPENAI_API_KEY missing or invalid length")
    return ok, warn


def active_ports() -> Tuple[List[int], List[str]]:
    ports: List[int] = []
    warnings: List[str] = []
    try:
        cmd = ["netstat", "-ano"]
        p = subprocess.run(cmd, capture_output=True, text=True)
        out = p.stdout
        for line in out.splitlines():
            if "LISTEN" in line.upper():
                parts = line.split()
                for token in parts:
                    if ":" in token and token.count(":") >= 1:
                        try:
                            prt = int(token.rsplit(":", 1)[-1])
                            ports.append(prt)
                        except Exception:
                            pass
        ports = sorted(set(ports))
    except Exception as e:
        warnings.append(f"netstat failed: {e}")
    return ports, warnings


async def run_audit() -> Dict[str, Any]:
    healthy: List[str] = []
    warnings: List[str] = []
    critical: List[str] = []

    route_checks, w1 = await probe_routes()
    warnings += w1
    if all(rc.ok for rc in route_checks):
        healthy.append("Core routes responsive")
    else:
        warnings.append("Some routes not responsive — see details.routes")

    deploys, w2 = await fetch_deployments()
    warnings += w2
    dep_health, w3 = await check_running_endpoints(deploys)
    warnings += w3
    if dep_health and all(d.get("ok") for d in dep_health if d):
        healthy.append("Running deployments respond at /hello")

    db_ok, db_err = db_integrity()
    if db_ok:
        healthy.append("DB integrity OK (read-write)")
    else:
        critical.append(f"DB error: {db_err}")

    deploy_dirs = list_deploy_dirs()
    present, missing = essential_files()
    if present:
        healthy.append("Essential files present")
    if missing:
        warnings.append("Missing files: " + ", ".join(missing))

    env_ok, env_warn = env_checks()
    healthy += env_ok
    warnings += env_warn

    ports, w4 = active_ports()
    warnings += w4

    if critical:
        overall = "CRITICAL"
    elif warnings:
        overall = "WARNING"
    elif healthy:
        overall = "EXCELLENT"
    else:
        overall = "GOOD"

    report = {
        "routes": [asdict(r) for r in route_checks],
        "deployments": deploys,
        "deployment_health": dep_health,
        "deploy_dirs": deploy_dirs,
        "ports": ports,
        "healthy": healthy,
        "warnings": warnings,
        "critical": critical,
        "overall": overall,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    log_dir = Path("deployments")
    log_dir.mkdir(exist_ok=True)
    with open(log_dir / f"system_audit_{ts}.log", "w", encoding="utf-8") as f:
        f.write(json.dumps(report, ensure_ascii=False, indent=2))

    return report


if __name__ == "__main__":
    rep = asyncio.run(run_audit())
    print(json.dumps(rep, ensure_ascii=False, indent=2))

