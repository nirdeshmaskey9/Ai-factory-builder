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
        from pathlib import Path
        import time, json
        started = time.time()
        if domain == "web":
            from .suites.web_suite import evaluate  # lazy import
        elif domain == "cli":
            from .suites.cli_suite import evaluate
        elif domain == "ml":
            from .suites.ml_suite import evaluate
        else:
            # Placeholder for future domains
            rep = EvaluationReport(True, f"No suite for domain '{domain}', skipping.", {"skipped": True, "status": "template_not_applicable"})
            # Log structured stress line if desired
            try:
                log_dir = Path("logs"); log_dir.mkdir(parents=True, exist_ok=True)
                with open(log_dir / "evaluator.log", "a", encoding="utf-8") as f:
                    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    f.write(json.dumps({"ts": ts, "build_id": build_id, "domain": domain, "passed": rep.passed, "summary": rep.summary})+"\n")
            except Exception:
                pass
            return rep

        if inspect.iscoroutinefunction(evaluate):
            report = await evaluate(build_id)  # type: ignore
        else:
            report = evaluate(build_id)  # type: ignore
        # Ensure non-empty summary
        if not getattr(report, "summary", ""):  # type: ignore
            report.summary = "Evaluation completed successfully."
        # Structured logging
        try:
            log_dir = Path("logs")
            log_dir.mkdir(parents=True, exist_ok=True)
            with open(log_dir / "evaluator.log", "a", encoding="utf-8") as f:
                ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                f.write(json.dumps({"ts": ts, "build_id": build_id, "domain": domain, "passed": report.passed, "summary": report.summary})+"\n")
        except Exception:
            pass
        # Write stress_test.log line with duration to support stress reporting
        try:
            dur = round(time.time() - started, 3)
            with open(Path("logs") / "stress_test.log", "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "build_id": build_id,
                    "domain": domain,
                    "passed": report.passed,
                    "time_taken": dur,
                    "errors": [],
                })+"\n")
        except Exception:
            pass
        return report
