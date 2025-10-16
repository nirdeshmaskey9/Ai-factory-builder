from __future__ import annotations

import math
import random
import time
import uuid
from typing import Dict, List, Tuple

from ai_factory.router_v2.router_v2_store import list_models, log_routing
from ai_factory.memory.memory_embeddings import add_to_memory


_TASK_TO_CAPS = {
    "planning": ["planning", "logic", "general"],
    "coding": ["coding", "reasoning", "general"],
    "design": ["design", "ui", "general"],
    "logic": ["logic", "general"],
    "testing": ["testing", "coding", "general"],
    "deployment": ["deployment", "general"],
    "general": ["general"],
}


def _score_model(task_type: str, model) -> float:
    caps = (model.capabilities or "").split(",")
    caps = [c.strip().lower() for c in caps if c.strip()]
    want = _TASK_TO_CAPS.get(task_type, ["general"])
    cap_match = any(c in caps for c in want)
    s_caps = 0.5 if cap_match else 0.2
    # lower latency is better; map to 0..1
    lat = max(1.0, float(model.avg_latency_ms))
    s_lat = max(0.0, min(1.0, 1.0 / (1.0 + lat / 600.0))) * 0.3
    # weight scaled
    s_w = max(0.0, min(1.0, float(model.weight) / 2.0)) * 0.2
    return s_caps + s_lat + s_w


def choose_model(task_type: str, seed: str | None = None) -> Tuple[str, float, float]:
    models = list_models()
    if not models:
        # should not happen due to seed; default
        return "gpt4", 0.5, 400.0

    base_scores = [(m.model_name, _score_model(task_type, m), m.avg_latency_ms) for m in models]
    # deterministic noise based on seed
    rnd = random.Random(seed or "router_v2")
    scored = []
    for name, sc, lat in base_scores:
        sc2 = max(0.0, min(1.0, sc + (rnd.random() - 0.5) * 0.05))
        scored.append((name, sc2, lat))
    chosen = max(scored, key=lambda t: t[1])
    return chosen  # (model_name, score, latency_ms)


def route(task_type: str, meta: Dict | None = None) -> Dict:
    dispatch_id = str(uuid.uuid4())
    t0 = time.time()
    model_name, score, lat = choose_model(task_type, seed=dispatch_id)
    # simulate decision duration close to expected latency fraction
    duration_ms = max(5.0, min(lat, 800.0))
    # log
    log_id = log_routing(task_type=task_type, model_name=model_name, duration_ms=duration_ms, score=score)
    # memory snippet
    snippet = (
        "[ROUTER v8]\n" f"task_type: {task_type}\n" f"chosen: {model_name}\n" f"duration_ms: {duration_ms:.1f}\n" f"score: {score:.3f}"
    )
    add_to_memory(f"route:{dispatch_id}", snippet)

    return {
        "dispatch_id": dispatch_id,
        "model_name": model_name,
        "score": score,
        "duration_ms": duration_ms,
        "decided_at": time.time(),
        "log_id": log_id,
    }

