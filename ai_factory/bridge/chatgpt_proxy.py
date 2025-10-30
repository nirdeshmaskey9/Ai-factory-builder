from __future__ import annotations

import os
import time
from typing import Dict, Any


def _mock_response(ceo: Dict[str, Any]) -> Dict[str, Any]:
    text = (
        "JoJo Bridge (mock):\n"
        f"You said: {ceo.get('user_text','')}\n\n"
        "Context considered:\n"
        f"{ceo.get('context_additions','')}\n"
    )
    return {"response_text": text, "model": ceo.get("target_model") or "mock"}


def call_chatgpt(ceo: Dict[str, Any], timeout_sec: int = 90) -> Dict[str, Any]:
    # Ephemeral by design; do not persist any raw content here.
    api_key = os.getenv("OPENAI_API_KEY")
    mode = os.getenv("JOJO_BRIDGE_MODE", "exact_relay").lower()
    model = os.getenv("JOJO_BRIDGE_MODEL", os.getenv("AI_FACTORY_CLOUD_MODEL", "gpt-4o"))
    if not api_key or "mock" in mode:
        return _mock_response(ceo)

    # Avoid recursive network calls; only single-shot outbound
    try:
        from openai import OpenAI  # type: ignore
        client = OpenAI(api_key=api_key)
        sys_prompt = (
            "You are the external reasoning engine for JoJo."
            " Respond naturally to the user_text. Consider the context_additions and memory_summary."
            " The user_text must be preserved in meaning and phrasing; do not overwrite wording."
        )
        messages = [
            {"role": "system", "content": sys_prompt},
            {
                "role": "user",
                "content": (
                    f"User text (verbatim):\n{ceo.get('sanitized_text') or ceo.get('user_text') or ''}\n\n"
                    f"Context additions:\n{ceo.get('context_additions','')}\n\n"
                    f"Memory summary:\n{ceo.get('memory_summary','')}"
                ),
            },
        ]
        t0 = time.time()
        # Single request with sane max-tokens
        resp = client.chat.completions.create(
            model=model or "gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=800,
            timeout=timeout_sec,
        )
        latency_ms = int((time.time() - t0) * 1000)
        text = resp.choices[0].message.content if resp and resp.choices else ""
        return {"response_text": text, "model": model, "latency_ms": latency_ms}
    except Exception:
        # Fallback to mock in error scenarios to keep pipeline robust
        return _mock_response(ceo)

