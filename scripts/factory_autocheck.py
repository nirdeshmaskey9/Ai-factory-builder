import socket, subprocess, time, sys, os

PORT = 8015


def is_port_open(port: int = PORT) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        s.connect(("127.0.0.1", port))
        s.close()
        return True
    except Exception:
        return False


def wait_until_ready(timeout: float = 15.0) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        if is_port_open():
            return True
        time.sleep(0.5)
    return False


def ensure_backend_running() -> bool:
    if is_port_open():
        print(f"🟢 Factory backend already running on port {PORT}")
        return True
    print("🔴 Factory backend not detected, attempting to start...")
    creationflags = 0
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
    subprocess.Popen([sys.executable, "-m", "uvicorn", "ai_factory.main:app", "--port", str(PORT)], creationflags=creationflags)
    if wait_until_ready():
        print("🟢 Factory backend started successfully.")
        return True
    print("❌ Could not start backend.")
    return False


if __name__ == "__main__":
    ensure_backend_running()

