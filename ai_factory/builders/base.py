"""Builder base interfaces and shared utilities.

Defines the `Builder` protocol and shared logic for scaffolding outputs,
rendering templates with Jinja2, and writing build manifests.
"""

from __future__ import annotations

import json
import os
import shutil
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
from pathlib import Path
import logging


@dataclass
class BuildResult:
    build_id: str
    outputs_path: str
    manifest_path: str
    warnings: list[str]


class Builder:
    """Abstract builder interface.

    Subclasses should implement `build_domain` and optionally override
    `render_template`.
    """

    def __init__(self, env: Any):
        self.env = env

    def build(self, blueprint: Mapping[str, Any], options: Mapping[str, Any] | None = None, ctx: Mapping[str, Any] | None = None) -> BuildResult:
        """Execute the build for a given domain.

        Returns a `BuildResult` containing paths and warnings.
        """
        build_id = uuid.uuid4().hex[:12]
        base_dir = Path("builds") / build_id
        inputs_dir = base_dir / "inputs"
        outputs_dir = base_dir / "outputs"
        logs_dir = base_dir / "logs"
        for d in (inputs_dir, outputs_dir, logs_dir):
            d.mkdir(parents=True, exist_ok=True)

        # Persist inputs for audit/rollback
        with open(inputs_dir / "blueprint.json", "w", encoding="utf-8") as f:
            json.dump(blueprint, f, ensure_ascii=False, indent=2)
        if options:
            with open(inputs_dir / "options.json", "w", encoding="utf-8") as f:
                json.dump(dict(options), f, ensure_ascii=False, indent=2)

        warnings: list[str] = []
        # Delegate
        try:
            self.build_domain(blueprint=blueprint, options=options or {}, ctx=ctx or {}, outputs_dir=outputs_dir, warnings=warnings)
        except Exception as e:
            warnings.append(f"build_error: {e}")
            try:
                log_dir = Path("logs")
                log_dir.mkdir(exist_ok=True)
                with open(log_dir / "build_errors.log", "a", encoding="utf-8") as f:
                    f.write(f"{build_id} {e}\n")
            except Exception:
                pass

        # Write manifest
        manifest = self._manifest(build_id=build_id, blueprint=blueprint, options=options or {}, outputs_dir=str(outputs_dir), warnings=warnings, ctx=ctx or {})
        manifest_path = base_dir / "manifest.json"
        # Atomic manifest write with fallback logging
        try:
            tmp = manifest_path.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)
            tmp.replace(manifest_path)
        except Exception as e:
            try:
                log_dir = Path("logs")
                log_dir.mkdir(parents=True, exist_ok=True)
                with open(log_dir / "factory_warnings.log", "a", encoding="utf-8") as lf:
                    lf.write(f"ERROR manifest_write: {manifest_path} -> {e}\n")
            except Exception:
                pass
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)

        return BuildResult(
            build_id=build_id,
            outputs_path=str(outputs_dir),
            manifest_path=str(manifest_path),
            warnings=warnings,
        )

    # ---- Methods for subclasses ----
    def build_domain(self, *, blueprint: Mapping[str, Any], options: Mapping[str, Any], ctx: Mapping[str, Any], outputs_dir: Path, warnings: list[str]) -> None:
        raise NotImplementedError

    # ---- Shared helpers ----
    def render_to_file(self, template_name: str, context: Mapping[str, Any], dest: Path) -> None:
        try:
            template = self.env.get_template(template_name)
            rendered = template.render(**context)
        except Exception as e:
            rendered = f"Generated file (fallback). Template '{template_name}' missing or failed: {e}\n"
            try:
                log_dir = Path("logs")
                log_dir.mkdir(parents=True, exist_ok=True)
                with open(log_dir / "factory_warnings.log", "a", encoding="utf-8") as lf:
                    lf.write(f"WARN template_render: {template_name} -> {e}\n")
            except Exception:
                pass
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".tmp")
        tmp.write_text(rendered, encoding="utf-8")
        tmp.replace(dest)

    def copy_tree(self, src_dir: Path, dest_dir: Path) -> None:
        if not src_dir.exists():
            return
        for root, _, files in os.walk(src_dir):
            rel = Path(root).relative_to(src_dir)
            for file in files:
                src_file = Path(root) / file
                dst_file = dest_dir / rel / file
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dst_file)

    def _manifest(self, *, build_id: str, blueprint: Mapping[str, Any], options: Mapping[str, Any], outputs_dir: str, warnings: list[str], ctx: Mapping[str, Any]) -> dict[str, Any]:
        from ai_factory import __version__ as pkg_version  # type: ignore
        version_file = Path("VERSION")
        version = version_file.read_text(encoding="utf-8").strip() if version_file.exists() else pkg_version
        # enumerate output files
        try:
            files = []
            for p in Path(outputs_dir).rglob("*"):
                if p.is_file():
                    try:
                        files.append(str(p.relative_to(outputs_dir)))
                    except Exception:
                        files.append(str(p))
        except Exception:
            files = []
        domain = str((ctx.get("metadata", {}) or {}).get("domain", "")) if isinstance(ctx, dict) else ""
        return {
            "build_id": build_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "pid": os.getpid(),
            "version": version,
            "goal": blueprint.get("goal"),
            "domain": domain or blueprint.get("domain"),
            "blueprint": dict(blueprint),
            "options": dict(options),
            "outputs_dir": outputs_dir,
            "files": files,
            "warnings": warnings,
        }
