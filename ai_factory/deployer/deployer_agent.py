from __future__ import annotations

from typing import Any, Dict, Optional
import os
import time
import httpx

from sqlalchemy import select, desc

from ai_factory.supervisor.supervisor_store import get_recent as supervisor_recent
from ai_factory.memory.memory_db import SessionLocal, SupervisorSession
from ai_factory.deployer.deployer_store import save_deployment, update_status, get_deployment
from ai_factory.services import deployer_service as svc
from ai_factory.memory.memory_embeddings import add_to_memory


def _resolve_session(session_id: Optional[int], goal: Optional[str]) -> Optional[SupervisorSession]:
    if session_id is not None:
        with SessionLocal() as session:
            stmt = select(SupervisorSession).where(SupervisorSession.id == session_id)
            return session.scalars(stmt).first()
    if goal:
        with SessionLocal() as session:
            stmt = select(SupervisorSession).where(SupervisorSession.goal.like(f"%{goal}%")).order_by(desc(SupervisorSession.timestamp)).limit(1)
            return session.scalars(stmt).first()
    # fallback latest
    rows = supervisor_recent(limit=1)
    return rows[0] if rows else None


def deploy(session_id: Optional[int] = None, goal: Optional[str] = None) -> Dict[str, Any]:
    # Ensure persistent deployments root
    DEPLOY_ROOT = os.path.join(os.getcwd(), "deployments")
    os.makedirs(DEPLOY_ROOT, exist_ok=True)
    sess = _resolve_session(session_id, goal)
    if not sess:
        raise ValueError("No supervisor session available for deployment")

    g = sess.goal or goal or "deployed-app"
    port = svc.find_free_port()
    endpoint = f"http://127.0.0.1:{port}"
    version = "v1.0.0"
    # Save deployment first to obtain ID and path
    # Initial status before launch
    dep_id = save_deployment(session_id=sess.id, goal=g, port=port, endpoint=endpoint, version=version, status="initializing")
    deploy_path = os.path.join(DEPLOY_ROOT, str(dep_id))
    os.makedirs(deploy_path, exist_ok=True)
    # Write app files into persistent directory
    path = svc.package_app(g, sess.id, dest=__import__('pathlib').Path(deploy_path))
    # Now launch the app from persistent directory
    proc = svc.launch_app(path, port)
    status = svc.check_status(proc)
    # Update status and store deploy path in notes
    update_status(dep_id, status, notes=f"path={deploy_path}")
    svc.register_process(dep_id, proc)
    # Log path to stdout for operator visibility
    try:
        print(f"📦 Deployment saved to: {deploy_path}")
    except Exception:
        print(f"[deploy] Deployment saved to: {deploy_path}")

    # Automatic verification: initial quick ping to /hello
    _ = verify_deployment(port)
    # Self-verification: probe /hello endpoint after short delay
    time.sleep(3)
    verify_notes = ""
    try:
        url = f"http://127.0.0.1:{port}/hello"
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(url)
        if resp.status_code == 200:
            msg = None
            try:
                msg = f"Verified: {resp.json()}"
            except Exception:
                msg = "Verified: 200 OK at /hello"
            try:
                print(f"✅ {msg}")
            except Exception:
                print(f"[deploy] {msg}")
            verify_notes = f"Verified OK at /hello (status={resp.status_code})"
        else:
            try:
                print(f"⚠️ Verification failed (status={resp.status_code})")
            except Exception:
                print(f"[deploy] Verification failed (status={resp.status_code})")
            verify_notes = f"Verification failed with status {resp.status_code}"
    except Exception as e:
        try:
            print(f"⚠️ Could not verify /hello endpoint: {e}")
        except Exception:
            print(f"[deploy] Could not verify /hello endpoint: {e}")
        verify_notes = f"Verification error: {e}"

    update_status(dep_id, "running", notes=verify_notes)

    # memory snippet
    snippet = svc.make_memory_snippet(g, port, version, status)
    add_to_memory(f"deploy:{dep_id}", snippet)

    return {"deployment_id": dep_id, "goal": g, "port": port, "endpoint": endpoint, "status": status}


def status(deployment_id: int) -> Dict[str, Any]:
    dep = get_deployment(deployment_id)
    if not dep:
        raise ValueError("deployment not found")
    proc = svc.get_process(deployment_id)
    if proc:
        st = svc.check_status(proc)
        if st != dep.status:
            update_status(deployment_id, st)
        return {"deployment_id": dep.id, "status": st, "port": dep.port, "endpoint": dep.endpoint}
    # if no proc in registry, assume stopped
    update_status(deployment_id, "stopped")
    return {"deployment_id": dep.id, "status": "stopped", "port": dep.port, "endpoint": dep.endpoint}


def rollback(deployment_id: int) -> Dict[str, Any]:
    dep = get_deployment(deployment_id)
    if not dep:
        raise ValueError("deployment not found")
    svc.stop_process(deployment_id)
    update_status(deployment_id, "stopped")
    return {"deployment_id": deployment_id, "status": "stopped"}


def verify_deployment(port: int) -> bool:
    time.sleep(3)
    try:
        r = httpx.get(f"http://127.0.0.1:{port}/hello", timeout=3)
        if r.status_code == 200:
            try:
                print(f"✅ Verified /hello: {r.json()}")
            except Exception:
                print("✅ Verified /hello: 200 OK")
            return True
        else:
            print(f"⚠️ /hello returned {r.status_code}")
            return False
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False
