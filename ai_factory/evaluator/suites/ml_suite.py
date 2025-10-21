from __future__ import annotations

from pathlib import Path
from ai_factory.evaluator.runner import EvaluationReport
import json


def evaluate(build_id: str) -> EvaluationReport:
    base = Path("builds") / build_id / "outputs"
    try:
        folders = [p for p in base.iterdir() if p.is_dir()]
        if not folders:
            return EvaluationReport(False, "No output folder found.", {})
        proj_dir = folders[0]
        nb = proj_dir / "starter.ipynb"
        if not nb.exists():
            return EvaluationReport(False, "starter.ipynb missing.", {"searched": str(proj_dir)})
        # Validate notebook JSON structure
        try:
            data = json.loads(nb.read_text(encoding="utf-8", errors="ignore"))
            has_cells = bool(data.get("cells"))
        except Exception:
            has_cells = False
        return EvaluationReport(True, "Notebook found (cells: %s)." % has_cells, {"path": str(nb), "cells": has_cells})
    except Exception as e:
        return EvaluationReport(False, f"ml eval error: {e}", {})
