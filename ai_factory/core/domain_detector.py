"""Domain Detector
Determines the target build domain (web, cli, ml, data, automation, desktop)
based on provided blueprint and optional metadata.

Deterministic rules for MVP. Designed for future ML-backed classification.
"""

from __future__ import annotations

from typing import Any
from typing_extensions import Literal

DomainLabel = Literal["web", "cli", "ml", "data", "automation", "desktop"]


class DomainDetector:
    """Rule-based domain detector with a pluggable interface.

    The detector inspects blueprint keys and metadata hints to classify the
    build request into one of the supported domains. Future extensions can
    replace or augment these rules with an ML model while keeping the same
    interface.
    """

    SUPPORTED: tuple[DomainLabel, ...] = (
        "web",
        "cli",
        "ml",
        "data",
        "automation",
        "desktop",
    )

    @staticmethod
    def detect(blueprint: dict[str, Any] | None, metadata: dict[str, Any] | None = None) -> DomainLabel:
        """Detect the domain for a build request.

        Args:
            blueprint: Structured blueprint describing the desired application.
            metadata: Optional auxiliary hints such as tags or user intent.

        Returns:
            A domain label from the supported set.

        Notes:
            - Deterministic rules only. No external I/O or model calls.
            - If no rule matches, defaults to "cli" for safety.
        """
        bp = blueprint or {}
        md = metadata or {}

        # Explicit domain override via metadata
        hint = str(md.get("domain", "")).strip().lower()
        if hint in DomainDetector.SUPPORTED:
            return hint  # trust explicit user or upstream selection

        # Simple rule heuristics
        keys = set(x.lower() for x in bp.keys())
        text_fields = " ".join(
            str(bp.get(k, "")) for k in ("description", "title", "summary", "goal")
        ).lower()

        def mentions(*words: str) -> bool:
            return any(w in text_fields for w in words)

        # Web: presence of pages/routes/ui/views/server hints
        if {"pages", "routes", "ui", "frontend"} & keys or mentions("web", "http", "ui", "browser"):
            return "web"

        # CLI: commands/args/flags hints
        if {"commands", "cli", "flags", "arguments"} & keys or mentions("cli", "command line"):
            return "cli"

        # ML: model/training/dataset hints
        if {"model", "training", "dataset", "pipeline"} & keys or mentions("train", "model", "ml"):
            return "ml"

        # Data: transformations/etl/sql hints
        if {"etl", "sql", "schema", "tables", "transform"} & keys or mentions("data", "etl", "warehouse"):
            return "data"

        # Automation: workflows/schedules/integrations hints
        if {"workflow", "schedule", "automation", "integrations"} & keys or mentions("bot", "automation", "cron"):
            return "automation"

        # Desktop: electron/qt/tk hints
        if {"desktop", "electron", "qt", "tk"} & keys or mentions("desktop", "windowed"):
            return "desktop"

        # Default fallback
        return "cli"

