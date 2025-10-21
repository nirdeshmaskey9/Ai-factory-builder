from __future__ import annotations

from pathlib import Path
from ai_factory.evaluator.runner import EvaluationReport


def evaluate(build_id: str) -> EvaluationReport:
    base = Path("builds") / build_id / "outputs"
    try:
        folders = [p for p in base.iterdir() if p.is_dir()]
        if not folders:
            return EvaluationReport(False, "No output folder found.", {})
        app_dir = folders[0]
        # Any .py file as entry point and contains argparse reference
        py_files = list(app_dir.glob("*.py"))
        if not py_files:
            return EvaluationReport(False, "No CLI entry (.py) found.", {"searched": str(app_dir)})
        entry = py_files[0]
        try:
            txt = entry.read_text(encoding="utf-8", errors="ignore")
            has_argparse = "argparse" in txt
        except Exception:
            has_argparse = False
        return EvaluationReport(True, "CLI entry detected (argparse: %s)." % has_argparse, {"entry": str(entry), "argparse": has_argparse})
    except Exception as e:
        return EvaluationReport(False, f"cli eval error: {e}", {})
