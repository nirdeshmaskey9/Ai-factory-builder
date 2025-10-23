import argparse
import os
from pathlib import Path


def organize(path: Path) -> int:
    if not path.exists() or not path.is_dir():
        print(f"[error] path not found: {path}")
        return 1
    count = 0
    for p in path.iterdir():
        if not p.is_file():
            continue
        ext = p.suffix.lower().lstrip(".") or "noext"
        dest_dir = path / ext
        dest_dir.mkdir(exist_ok=True)
        try:
            p.rename(dest_dir / p.name)
            count += 1
        except Exception as e:
            print(f"[warn] could not move {p.name}: {e}")
    print(f"Moved {count} files.")
    return 0


def main():
    ap = argparse.ArgumentParser(prog="file_organizer_cli", description="automation CLI tool to sort files by type into folders")
    ap.add_argument("--path", required=True, help="Folder to organize")
    args = ap.parse_args()
    return organize(Path(args.path))


if __name__ == "__main__":
    raise SystemExit(main())

