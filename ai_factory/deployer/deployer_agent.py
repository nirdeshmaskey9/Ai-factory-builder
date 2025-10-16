from __future__ import annotations

from typing import Any, Dict, Optional

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
    sess = _resolve_session(session_id, goal)
    if not sess:
        raise ValueError("No supervisor session available for deployment")

    g = sess.goal or goal or "deployed-app"
    path = svc.package_app(g, sess.id)
    port = svc.find_free_port()
    proc = svc.launch_app(path, port)
    status = svc.check_status(proc)
    endpoint = f"http://127.0.0.1:{port}"
    version = "v1.0.0"

    dep_id = save_deployment(session_id=sess.id, goal=g, port=port, endpoint=endpoint, version=version, status=status)
    svc.register_process(dep_id, proc)

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

