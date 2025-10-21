from __future__ import annotations

import glob
import json
import os
from fastapi import APIRouter


router = APIRouter(tags=["system-report"])


@router.get("/system/report")
def get_last_report():
    """Return the latest stress summary JSON file if available."""
    os.makedirs("logs", exist_ok=True)
    reports = glob.glob("logs/stress_*.json")
    if not reports:
        return {"detail": "No stress reports found."}
    latest = max(reports, key=os.path.getmtime)
    with open(latest, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return {"detail": f"Could not parse {latest}"}

