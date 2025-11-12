from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from ai_factory.builders.base import Builder


class CliBuilder(Builder):
    def build_domain(self, *, blueprint: Mapping[str, Any], options: Mapping[str, Any], ctx: Mapping[str, Any], outputs_dir: Path, warnings: list[str]) -> None:
        name = str(blueprint.get("name") or blueprint.get("title") or "cli_app").replace(" ", "_")
        text_fields = " ".join(
            str(blueprint.get(k, "")) for k in ("description", "title", "summary", "goal")
        ).lower()

        # Keyword-based selection for automation CLI
        if any(k in text_fields for k in ("automation", "organize", "organizer")):
            self._build_automation_cli(name=name, outputs_dir=outputs_dir, warnings=warnings, description=str(blueprint.get("description", "Automation CLI")))
            return
        context = {
            "app_name": name,
            "description": blueprint.get("description", "A generated CLI app."),
            "entry": blueprint.get("entry", f"{name}.py"),
        }
        # Python CLI script + README (paths relative to cli template root)
        self.render_to_file("cli.py.j2", context, outputs_dir / name / context["entry"])
        self.render_to_file("README.md.j2", context, outputs_dir / name / "README.md")

    def _build_automation_cli(self, *, name: str, outputs_dir: Path, warnings: list[str], description: str) -> None:
        root = Path("ai_factory") / "templates" / "automation_cli"
        if not root.exists():
            warnings.append("automation_cli template missing")
            return
        tokens = {
            "__APP_NAME__": name,
            "__DESCRIPTION__": description,
        }
        base = outputs_dir / name
        for p in root.rglob("*"):
            if p.is_dir():
                continue
            rel = p.relative_to(root)
            if p.suffix == ".tmpl":
                dest = base / rel.with_suffix("")
                text = p.read_text(encoding="utf-8")
                for k, v in tokens.items():
                    text = text.replace(k, str(v))
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(text, encoding="utf-8")
            else:
                dest = base / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(p.read_bytes())
