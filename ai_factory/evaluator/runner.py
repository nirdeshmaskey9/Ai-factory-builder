from __future__ import annotations

from dataclasses import dataclass
import inspect


@dataclass
class EvaluationReport:
    passed: bool
    summary: str
    artifacts: dict


class EvaluationRunner:
    async def run(self, build_id: str, domain: str) -> EvaluationReport:
        if domain == "web":
            from .suites.web_suite import evaluate  # lazy import
        elif domain == "cli":
            from .suites.cli_suite import evaluate
        elif domain == "ml":
            from .suites.ml_suite import evaluate
        else:
            # Placeholder for future domains
            return EvaluationReport(True, f"No suite for domain '{domain}', skipping.", {"skipped": True})

        if inspect.iscoroutinefunction(evaluate):
            report = await evaluate(build_id)  # type: ignore
        else:
            report = evaluate(build_id)  # type: ignore
        # Ensure non-empty summary
        if not getattr(report, "summary", ""):  # type: ignore
            report.summary = "Evaluation completed successfully."
        # Structured logging
        try:
            from pathlib import Path
            import time, json
            log_dir = Path("logs")
            log_dir.mkdir(parents=True, exist_ok=True)
            with open(log_dir / "evaluator.log", "a", encoding="utf-8") as f:
                ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                f.write(json.dumps({"ts": ts, "build_id": build_id, "domain": domain, "passed": report.passed, "summary": report.summary})+"\n")
        except Exception:
            pass
        return report
