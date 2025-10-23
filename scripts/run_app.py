from __future__ import annotations

import os
import subprocess
from pathlib import Path


def find_output_apps() -> list[Path]:
    roots: list[Path] = []
    builds = Path("builds")
    if not builds.exists():
        return roots
    for bid in sorted(builds.iterdir(), reverse=True):
        if not bid.is_dir():
            continue
        out = bid / "outputs"
        if out.exists():
            for app_dir in out.iterdir():
                if app_dir.is_dir():
                    roots.append(app_dir)
    return roots


def choose(options: list[str]) -> int | None:
    for i, label in enumerate(options, 1):
        print(f"{i}. {label}")
    try:
        raw = input("Select app number to run (Enter to cancel): ").strip()
        if not raw:
            return None
        idx = int(raw)
    except Exception:
        print("Invalid selection.")
        return None
    if 1 <= idx <= len(options):
        return idx - 1
    print("Out of range.")
    return None


def run_uvicorn(app_dir: Path) -> int:
    # Detect app entry
    main_py = app_dir / "main.py"
    app_py = app_dir / "app.py"
    if main_py.exists():
        module = "main:app"
    elif app_py.exists():
        module = "app:app"
    else:
        print(f"No main.py or app.py in {app_dir}")
        return 2
    env = dict(os.environ)
    print(f"Launching uvicorn {module} in {app_dir} (Ctrl+C to stop)")
    try:
        return subprocess.call(["python", "-m", "uvicorn", module, "--reload"], cwd=str(app_dir), env=env)
    except FileNotFoundError:
        print("uvicorn not installed. Try: pip install uvicorn[standard]")
        return 3


def main() -> int:
    apps = find_output_apps()
    if not apps:
        print("No generated apps found under builds/*/outputs/")
        return 1
    labels = [str(p) for p in apps]
    idx = choose(labels)
    if idx is None:
        print("Cancelled.")
        return 0
    return run_uvicorn(apps[idx])


if __name__ == "__main__":
    raise SystemExit(main())

