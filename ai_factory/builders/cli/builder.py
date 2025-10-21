from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from ai_factory.builders.base import Builder


class CliBuilder(Builder):
    def build_domain(self, *, blueprint: Mapping[str, Any], options: Mapping[str, Any], ctx: Mapping[str, Any], outputs_dir: Path, warnings: list[str]) -> None:
        name = str(blueprint.get("name") or blueprint.get("title") or "cli_app").replace(" ", "_")
        context = {
            "app_name": name,
            "description": blueprint.get("description", "A generated CLI app."),
            "entry": blueprint.get("entry", f"{name}.py"),
        }
        # Python CLI script + README (paths relative to cli template root)
        self.render_to_file("cli.py.j2", context, outputs_dir / name / context["entry"])
        self.render_to_file("README.md.j2", context, outputs_dir / name / "README.md")
