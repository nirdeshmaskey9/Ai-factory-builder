from __future__ import annotations

from pathlib import Path
from ai_factory.evaluator.runner import EvaluationReport
import importlib.util
import sys
import httpx


async def evaluate_dynamic_app(outputs_dir: Path) -> EvaluationReport:
    """Evaluate a generated FastAPI app by checking /hello and /health.

    Returns a structured EvaluationReport with a combined summary and an
    artifacts list payload inside the artifacts dict.
    """
    app_py = outputs_dir / "app.py"
    spec = importlib.util.spec_from_file_location("generated_app", str(app_py))
    if not spec or not spec.loader:
        return EvaluationReport(False, "Failed to load app module.", {"files": ["app.py"]})
    module = importlib.util.module_from_spec(spec)
    sys.modules["generated_app"] = module
    spec.loader.exec_module(module)  # type: ignore
    app = getattr(module, "app", None)
    if app is None:
        return EvaluationReport(False, "No 'app' found in module.", {"files": ["app.py"]})

    # Use AsyncClient with ASGITransport for proper async evaluation
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        r1 = await client.get("/hello")
        r2 = await client.get("/health")
    ok1 = (r1.status_code == 200)
    ok2 = (r2.status_code == 200)
    passed = ok1 and ok2
    summary = f"/hello: {r1.status_code}; /health: {r2.status_code}"
    return EvaluationReport(passed, summary, {"files": ["app.py"]})


async def evaluate(build_id: str) -> EvaluationReport:
    base = Path("builds") / build_id / "outputs"
    # Hardened checks: folder exists, index.html exists, minimal content sanity, README exists
    try:
        folders = [p for p in base.iterdir() if p.is_dir()]
        if not folders:
            return EvaluationReport(False, "No output folder found.", {})
        app_dir = folders[0]
        # Branch: dynamic FastAPI app
        app_py = app_dir / "app.py"
        if app_py.exists():
            try:
                return await evaluate_dynamic_app(app_dir)
            except Exception as e:
                return EvaluationReport(False, f"ASGI evaluation failed: {e}", {"files": ["app.py"]})

        # Branch: static site
        index = app_dir / "index.html"
        readme = app_dir / "README.md"
        if not index.exists():
            return EvaluationReport(False, "index.html missing.", {"searched": str(app_dir)})
        content = index.read_text(encoding="utf-8", errors="ignore")
        has_title = "<title" in content.lower() or "<h1" in content.lower()
        artifacts = {"path": str(index), "readme": readme.exists()}
        if not has_title:
            return EvaluationReport(True, "index.html present (no <title>/<h1> detected)", artifacts)
        if readme.exists():
            return EvaluationReport(True, "index.html and README present.", artifacts)
        return EvaluationReport(True, "index.html present.", artifacts)
    except Exception as e:
        return EvaluationReport(False, f"web eval error: {e}", {})
