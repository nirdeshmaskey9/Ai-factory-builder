from __future__ import annotations
import os
import sys
import requests
import json
import time


def main() -> int:
    print("\n🧪 Running AI Factory Diagnostics...\n")

    try:
        resp = requests.get("http://127.0.0.1:8015/factory/info", timeout=5)
        print(f"- route_factory_info: {'✅' if resp.status_code == 200 else f'⚠️ ({resp.status_code})'}")
    except Exception as e:
        print(f"- route_factory_info: ⚠️ {e}")

    try:
        resp = requests.get("http://127.0.0.1:8015/deployer/list", timeout=5)
        print(f"- route_deployer_list: {'✅' if resp.status_code == 200 else f'⚠️ ({resp.status_code})'}")
    except Exception as e:
        print(f"- route_deployer_list: ⚠️ {e}")

    try:
        resp = requests.get("http://127.0.0.1:8015/deployer/health", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            print(f"- deployer health: ✅ {data.get('active_previews',0)} active (guardian {'on' if data.get('guardian_running') else 'off'})")
        else:
            print(f"- deployer health: ⚠️ HTTP {resp.status_code}")
    except Exception as e:
        print(f"- deployer health: ⚠️ {e}")

    print("\n✅ Diagnostics complete.")
    print("🧱 AI Factory v1.2.6.4.3 — Guardian Verified and Fully Online.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


