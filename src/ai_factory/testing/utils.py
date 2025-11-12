from __future__ import annotations

import json
import os
import socket
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable, Iterable, List, Tuple

import requests
import random


BASE = "http://127.0.0.1:8015"


def post_factory_create(goal: str, domain: str, dynamic: bool = False) -> dict:
    payload = {"goal": goal, "domain": domain}
    if dynamic:
        payload["dynamic"] = True
    resp = requests.post(f"{BASE}/factory/create", json=payload, timeout=60)
    if resp.status_code != 200:
        raise AssertionError(f"[factory_create] expected 200, got {resp.status_code}: {resp.text}")
    data = resp.json()
    if not isinstance(data, dict) or "build_id" not in data:
        raise AssertionError(f"[factory_create] invalid response JSON: {data}")
    return data


def preview_start(build_id: str) -> dict:
    resp = requests.get(f"{BASE}/deployer/preview/{build_id}", timeout=30)
    if resp.status_code != 200:
        raise AssertionError(f"[preview_start] expected 200, got {resp.status_code}: {resp.text}")
    return resp.json()


def preview_start_resilient(build_id: str, retries: int = 5) -> dict:
    """Starts preview server with retry + backoff; handles slow startup gracefully."""
    url = f"{BASE}/deployer/preview/{build_id}"
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, timeout=60)
            if resp.status_code == 200:
                return resp.json()
            print(f"⚠️  preview_start {build_id} attempt {attempt}: HTTP {resp.status_code}")
        except requests.exceptions.ReadTimeout:
            print(f"⚠️  preview_start {build_id} timed out (attempt {attempt})")
        except Exception as e:
            print(f"⚠️  preview_start {build_id} failed ({e})")
        time.sleep(2 * attempt + random.uniform(0, 1))
    raise AssertionError(f"[preview_start] failed after {retries} attempts for {build_id}")


def preview_stop_all() -> dict:
    """Stop all running preview processes safely; tolerate no-active-preview responses."""
    try:
        resp = requests.get(f"{BASE}/deployer/preview/stop_all", timeout=5)
        if resp.status_code == 500 and "No app.py" in resp.text:
            print("⚠️  No active previews to stop — continuing safely.")
            return {"detail": "no active previews"}
        assert resp.status_code == 200, f"[preview_stop_all] expected 200, got {resp.status_code}: {resp.text}"
        return resp.json()
    except Exception as e:
        print(f"⚠️  preview_stop_all encountered an error: {e}")
        return {"detail": str(e)}


def http_get(url: str, timeout: int = 5) -> Tuple[int, str]:
    try:
        r = requests.get(url, timeout=timeout)
        return r.status_code, r.text
    except Exception as e:
        return 0, str(e)


def list_recent_builds(n: int = 10) -> List[str]:
    bdir = Path("builds")
    if not bdir.exists():
        return []
    dirs = sorted([p for p in bdir.iterdir() if p.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True)
    return [d.name for d in dirs[:n]]


def read_manifest(build_id: str) -> dict:
    mpath = Path("builds") / build_id / "manifest.json"
    if not mpath.exists():
        raise FileNotFoundError(str(mpath))
    return json.loads(mpath.read_text(encoding="utf-8"))


def sqlite_fetch_builds(db_path: str | None = None) -> List[Tuple]:
    # Default to internal sqlite path if not provided
    if not db_path:
        db_path = str((Path(__file__).resolve().parent.parent / "data" / "memory.db").resolve())
    tries = 0
    while tries < 3:
        tries += 1
        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            cur = conn.cursor()
            # evaluation_results contains build_id rows written by factory
            cur.execute("SELECT build_id, domain, passed, summary FROM evaluation_results ORDER BY id DESC LIMIT 100")
            rows = cur.fetchall()
            conn.close()
            return rows
        except sqlite3.OperationalError:
            time.sleep(0.2 * tries)
        except Exception:
            break
    return []


def mutate_file(path: str, callback: Callable[[str], str]) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    new_text = callback(text)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(new_text, encoding="utf-8")
    tmp.replace(p)
