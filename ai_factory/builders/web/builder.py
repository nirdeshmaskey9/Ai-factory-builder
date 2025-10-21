from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from ai_factory.builders.base import Builder


class WebBuilder(Builder):
    def build_domain(self, *, blueprint: Mapping[str, Any], options: Mapping[str, Any], ctx: Mapping[str, Any], outputs_dir: Path, warnings: list[str]) -> None:
        name = str(blueprint.get("name") or blueprint.get("title") or "web_app").replace(" ", "_")
        text_fields = " ".join(
            str(blueprint.get(k, "")) for k in ("description", "title", "summary", "goal")
        ).lower()
        md = ctx.get("metadata", {}) if isinstance(ctx, dict) else {}
        is_dynamic = bool(
            blueprint.get("routes")
            or md.get("dynamic")
            or ("fastapi" in text_fields or "/hello" in text_fields)
        )

        if is_dynamic:
            context = {
                "app_name": name,
                "hello_text": blueprint.get("hello_text", f"Hello from {name}"),
                "route_path": blueprint.get("route", "/hello"),
                "description": blueprint.get("description", "A generated FastAPI app."),
            }
            base = outputs_dir / name
            self.render_to_file("dynamic/app.py.j2", context, base / "app.py")
            self.render_to_file("dynamic/README.md.j2", context, base / "README.md")
            self.render_to_file("dynamic/Dockerfile.j2", context, base / "Dockerfile")
        else:
            context = {
                "app_name": name,
                "title": blueprint.get("title", name),
                "description": blueprint.get("description", "A generated web app."),
            }
            # Static HTML + minimal README (paths relative to web template root)
            self.render_to_file("index.html.j2", context, outputs_dir / name / "index.html")
            self.render_to_file("README.md.j2", context, outputs_dir / name / "README.md")
