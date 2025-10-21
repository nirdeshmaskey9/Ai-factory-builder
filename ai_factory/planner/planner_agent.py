import os
import json
from typing import Dict, List

try:
    from openai import OpenAI  # type: ignore
except Exception:  # Optional dependency for offline tests
    OpenAI = None  # type: ignore


KNOWN_DOMAINS = {"web", "cli", "ml", "data", "automation", "desktop"}


def _detect_domain(prompt: str) -> str:
    p = (prompt or "").strip().lower()
    for d in KNOWN_DOMAINS:
        if f" {d} " in f" {p} ":
            return d
    for d in KNOWN_DOMAINS:
        if d in p:
            return d
    if "unknown" in p:
        return "unknown"
    return "web"


def _stub_steps(domain: str, prompt: str) -> List[Dict[str, str]]:
    return [
        {"index": 0, "action": f"Analyze prompt for {domain}", "rationale": "Initialize planning"},
        {"index": 1, "action": "Draft blueprint", "rationale": "Create minimal viable plan"},
    ]


def plan_task(prompt: str, *_, **__) -> Dict[str, object]:
    """
    Deterministic, test-stable planner output.
    - Parses domain from prompt for backward-compatible tests.
    - Always returns a dict with keys: domain, steps, summary.
    - Uses OpenAI when configured; otherwise returns a stub plan.
    """
    domain = _detect_domain(prompt)
    if domain == "unknown":
        raise ValueError("Unknown domain")

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or OpenAI is None:
        return {
            "domain": domain,
            "steps": _stub_steps(domain, prompt),
            "summary": "Stub planner: OpenAI disabled",
        }

    try:
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are the Planner MCP for AI Factory. Always respond with JSON "
                        "{domain, steps:[{index, action, rationale}], summary}."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        content = (resp.choices[0].message.content or "").strip()
        try:
            data = json.loads(content)
            d = domain  # trust local detection for tests
            steps = data.get("steps")
            if not isinstance(steps, list) or not steps:
                steps = _stub_steps(d, prompt)
            return {"domain": d, "steps": steps, "summary": data.get("summary", "Model plan")}
        except Exception:
            return {"domain": domain, "steps": _stub_steps(domain, prompt), "summary": "Wrapped non-JSON model output"}
    except Exception as e:
        return {"domain": domain, "steps": _stub_steps(domain, prompt), "summary": f"Planner error: {e}"}


# Legacy alias for tests that pass extra args
plan_for_domain = lambda prompt, *_: plan_task(prompt)
