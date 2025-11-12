from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List


LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
STRESS_LOG = LOG_DIR / "stress_test.log"
SUMMARY_JSON = LOG_DIR / "stress_summary.json"


def log_stress_result(*, build_id: str, domain: str, passed: bool, time_taken: float, errors: List[str] | None = None, extra: Dict[str, Any] | None = None) -> None:
    """Append a single stress test result line to logs/stress_test.log (JSONL)."""
    payload: Dict[str, Any] = {
        "build_id": build_id,
        "domain": domain,
        "passed": bool(passed),
        "time_taken": float(time_taken),
        "errors": errors or [],
    }
    if extra:
        payload.update(extra)
    STRESS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with STRESS_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _read_lines(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    return rows


def generate_stress_report() -> Dict[str, Any]:
    """Aggregate logs/stress_test.log into logs/stress_summary.json with key metrics.

    Returns the dictionary that was written to JSON.
    """
    rows = _read_lines(STRESS_LOG)
    total = len(rows)
    if total == 0:
        summary = {
            "total": 0,
            "success": 0,
            "fail": 0,
            "avg_build_duration": 0.0,
            "avg_success_rate": 0.0,
            "top_error_patterns": [],
            "files_causing_failures": [],
        }
        SUMMARY_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return summary

    success = sum(1 for r in rows if r.get("passed") is True)
    fail = total - success
    avg_dur = sum(float(r.get("time_taken", 0.0)) for r in rows) / max(total, 1)
    avg_success_rate = round((success / total) * 100.0, 2)

    # Error pattern aggregation
    err_counter: Counter[str] = Counter()
    for r in rows:
        for e in r.get("errors", []) or []:
            err_counter[e] += 1
    top_error_patterns = [
        {"pattern": k, "count": v} for k, v in err_counter.most_common(5)
    ]

    # Inspect last manifests for files frequently mentioned in summaries
    files_counter: Counter[str] = Counter()
    builds_dir = Path("builds")
    for r in rows:
        bid = r.get("build_id")
        if not bid:
            continue
        m = builds_dir / str(bid) / "manifest.json"
        try:
            data = json.loads(m.read_text(encoding="utf-8")) if m.exists() else {}
            for f in (data.get("files") or []):
                if any(x in str(f).lower() for x in ("main.py", "app.py", "routes", "templates")):
                    files_counter[str(f)] += 1
        except Exception:
            continue

    summary = {
        "total": total,
        "success": success,
        "fail": fail,
        "avg_build_duration": round(avg_dur, 3),
        "avg_success_rate": avg_success_rate,
        "top_error_patterns": top_error_patterns,
        "files_causing_failures": [
            {"file": k, "count": v} for k, v in files_counter.most_common(5)
        ],
    }
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary

