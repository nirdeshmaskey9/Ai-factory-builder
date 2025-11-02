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
    # Temporary stable model until gpt-5 is generally available
    model = "gpt-4o"
    try:
        # Runtime override from control panel
        from ai_factory.config_runtime_flags import mock_mode as _MOCK
    except Exception:
        _MOCK = False
    if _MOCK or (not api_key) or ("mock" in mode):
        return _mock_response(ceo)

    # Avoid recursive network calls; only single-shot outbound
    try:
        from openai import OpenAI  # type: ignore
        client = OpenAI(api_key=api_key)
        sys_prompt = "You are JoJo’s external reasoning engine."
        # Compose a single prompt string from ceo
        prompt = str(ceo.get("sanitized_text") or ceo.get("user_text") or "")
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": prompt},
        ]
        t0 = time.time()
        # Single request with aligned API payload
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
        )
        latency_ms = int((time.time() - t0) * 1000)
        text = resp.choices[0].message.content if resp and resp.choices else ""
        try:
            print(f"[GPT-5 Bridge] ✅ Response received ({len(text)} chars)")
        except Exception:
            pass
        # Usage accounting (best-effort)
        try:
            total_tokens = int(getattr(resp, 'usage', None).total_tokens)  # type: ignore[attr-defined]
        except Exception:
            try:
                total_tokens = int((resp.usage or {}).get('total_tokens', 0))  # type: ignore[attr-defined]
            except Exception:
                total_tokens = 0
        try:
            from ai_factory.config_runtime_flags import add_usage
            # Approximate pricing: $0.01 per 1K tokens
            add_usage(total_tokens, (total_tokens / 1000.0) * 0.01)
        except Exception:
            pass
        return {"response_text": text, "model": model, "latency_ms": latency_ms}
    except Exception:
        # Fallback to mock in error scenarios to keep pipeline robust
        return _mock_response(ceo)
