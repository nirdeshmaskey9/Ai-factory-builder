import os
try:
    from openai import OpenAI  # type: ignore
except Exception:  # Optional dependency
    OpenAI = None  # type: ignore

def plan_task(prompt: str):
    """
    Generates detailed build blueprints using GPT-4o for AI Factory apps.
    Supports web, CLI, and ML domains.
    """
    api_key = os.getenv('OPENAI_API_KEY', '')
    if not api_key or OpenAI is None:
        # Fallback: return a deterministic stub when OpenAI is not configured
        return (
            "[stub-planner] OpenAI disabled or missing. "
            f"Prompt length={len(prompt)}; returning no-op plan."
        )
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[
            {'role': 'system', 'content': (
                'You are the Planner MCP for AI Factory. '
                'Generate complete, auditable code blueprints for apps, '
                'including FastAPI backend, Jinja2 HTML templates, JS, CSS, and data files. '
                'Structure outputs cleanly under /builds/<id>/outputs/.'
            )},
            {'role': 'user', 'content': prompt}
        ],
        temperature=0.65
    )
    return response.choices[0].message.content.strip()
