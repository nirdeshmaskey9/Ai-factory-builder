import subprocess
import sys
import os


def main() -> None:
    try:
        print("🚀 Launching AI Factory (Auto Port Recovery Enabled)...")
    except Exception:
        print("Launching AI Factory (Auto Port Recovery Enabled)...")
    try:
        # Delegate to module entrypoint that performs port auto-recovery
        result = subprocess.call([sys.executable, "-m", "ai_factory.main"], env=os.environ.copy())
        sys.exit(result)
    except KeyboardInterrupt:
        print("\n🧩 Factory stopped by user.")
    except Exception as e:
        print(f"❌ Error launching Factory: {e}")


if __name__ == "__main__":
    main()
