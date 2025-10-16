from __future__ import annotations

import os
from typing import Optional

from ai_factory.memory.memory_embeddings import add_to_memory


def _has(var: str) -> bool:
    v = os.getenv(var, "").strip()
    return bool(v)


def gpt4o_chat(prompt: str, system: str = "You are a senior software architect.") -> str:
    try:
        if not _has("OPENAI_API_KEY"):
            return "[model-not-configured] OPENAI_API_KEY missing"
        from openai import OpenAI  # type: ignore

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        r = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        text = (r.choices[0].message.content or "").strip()
        add_to_memory("model:gpt4o", f"[MODEL v11]\ncomponent: model_clients\nmodel: gpt-4o\nprompt_preview: {prompt[:120]}")
        return text
    except Exception as e:  # pragma: no cover - optional path
        return f"[model-error] gpt4o_chat failed: {e}"


def claude3_chat(prompt: str, system: str = "You are a helpful code assistant.") -> str:
    try:
        if not _has("ANTHROPIC_API_KEY"):
            return "[model-not-configured] ANTHROPIC_API_KEY missing"
        import anthropic  # type: ignore

        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        r = client.messages.create(
            model="claude-3-sonnet-20240229",
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
        )
        text = getattr(r.content[0], "text", "") if getattr(r, "content", None) else ""
        add_to_memory("model:claude3", f"[MODEL v11.5]\ncomponent: model_clients\nmodel: claude-3-sonnet\nprompt_preview: {prompt[:120]}")
        return text
    except Exception as e:  # pragma: no cover - optional path
        return f"[model-error] claude3_chat failed: {e}"


def gemini_chat(prompt: str, system: str = "You are a creative UI/UX assistant.") -> str:
    try:
        if not _has("GOOGLE_API_KEY"):
            return "[model-not-configured] GOOGLE_API_KEY missing"
        import google.generativeai as genai  # type: ignore

        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel("gemini-1.5-pro")
        r = model.generate_content(f"{system}\nUser: {prompt}")
        text = getattr(r, "text", "")
        add_to_memory("model:gemini", f"[MODEL v11.5]\ncomponent: model_clients\nmodel: gemini-1.5-pro\nprompt_preview: {prompt[:120]}")
        return text
    except Exception as e:  # pragma: no cover - optional path
        return f"[model-error] gemini_chat failed: {e}"

