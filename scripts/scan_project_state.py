import os, json, subprocess, datetime
from pathlib import Path


def gather_structure(root_dir: Path, depth=4):
    tree = {}
    try:
        for item in root_dir.iterdir():
            name = item.name
            if name.startswith('.') or name.startswith('__pycache__'):
                continue
            if item.is_dir():
                if depth > 0:
                    tree[name] = gather_structure(item, depth-1)
                else:
                    tree[name] = '[...]'
            else:
                tree[name] = 'file'
    except Exception as e:
        tree['__error__'] = str(e)
    return tree


def main():
    root = Path(__file__).resolve().parents[1]
    timestamp = datetime.datetime.now().isoformat(timespec='seconds')

    report = {
        "timestamp": timestamp,
        "root": str(root),
        "version": None,
        "phase_markers": {},
        "structure": {},
        "installed_packages": None,
    }

    # 1) Version
    version_file = root / "ai_factory" / "version.py"
    if version_file.exists():
        try:
            report["version"] = version_file.read_text(errors="ignore").strip()
        except Exception as e:
            report["version"] = f"error reading version.py: {e}"

    # 2) Phase Markers
    log_dir = root / "ai_factory" / "data" / "logs"
    if log_dir.exists():
        for f in log_dir.glob("_codex_phase*.marker"):
            try:
                report["phase_markers"][f.name] = f.read_text(errors="ignore")
            except Exception as e:
                report["phase_markers"][f.name] = f"error: {e}"

    # 3) Structure (depth 4)
    report["structure"] = gather_structure(root)

    # 4) Pip Freeze
    try:
        pkgs = subprocess.check_output(["pip", "freeze"], text=True)
        report["installed_packages"] = pkgs.splitlines()
    except Exception as e:
        report["installed_packages"] = [f"Error retrieving packages: {e}"]

    # 5) Save Reports
    out_dir = root / "deployments" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "project_state_v3.4.3.json"
    md_path = out_dir / "project_state_v3.4.3.md"

    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(report, jf, indent=2)

    with open(md_path, "w", encoding="utf-8") as mf:
        mf.write(f"# Project State Report – {timestamp}\n\n")
        mf.write("## Version\n```python\n" + str(report["version"]) + "\n```\n\n")
        mf.write("## Phase Markers\n```json\n" + json.dumps(report["phase_markers"], indent=2) + "\n```\n\n")
        mf.write("## Directory Tree (Depth 4)\n")
        mf.write(json.dumps(report["structure"], indent=2))
        mf.write("\n\n## Installed Packages\n```\n" + "\n".join(report["installed_packages"] or []) + "\n```\n")

    print(f"✅ Project state report saved to {json_path}")
    print(f"✅ Markdown summary saved to {md_path}")


if __name__ == "__main__":
    main()

