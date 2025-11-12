from __future__ import annotations

from pathlib import Path
from typing import Dict


class TemplateRegistry:
    """Maps domain names to template directories within the repository."""

    def __init__(self) -> None:
        self._paths: Dict[str, Path] = {
            "web": Path("ai_factory/templates/web"),
            "cli": Path("ai_factory/templates/cli"),
            "ml": Path("ai_factory/templates/ml"),
            # Placeholders for future domains
            "data": Path("ai_factory/templates/data"),
            "automation": Path("ai_factory/templates/automation"),
            "desktop": Path("ai_factory/templates/desktop"),
        }

    def get_path(self, domain: str) -> Path:
        path = self._paths.get(domain)
        if not path:
            raise KeyError(f"Unknown domain templates: {domain}")
        return path

