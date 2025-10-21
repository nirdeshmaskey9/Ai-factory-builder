from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from ai_factory.builders.base import Builder


class DesktopBuilder(Builder):
    def build_domain(self, *, blueprint: Mapping[str, Any], options: Mapping[str, Any], ctx: Mapping[str, Any], outputs_dir: Path, warnings: list[str]) -> None:
        name = str(blueprint.get("name") or blueprint.get("title") or "desktop_app").replace(" ", "_")
        context = {
            "project_name": name,
            "description": blueprint.get("description", "A generated desktop app scaffold."),
        }
        self.render_to_file("README.md.j2", context, outputs_dir / name / "README.md")

