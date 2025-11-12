from __future__ import annotations

from typing import Dict, Any

from ai_factory.services.router_v2_service import route as do_route


def route_task(task_type: str, meta: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return do_route(task_type, meta)

