from __future__ import annotations

import socket


def find_free_port(start_port: int, max_port: int) -> int:
    """Find a free TCP port in [start_port, max_port].

    Attempts to bind on 127.0.0.1 to detect availability. Raises RuntimeError
    if no free port is found in the given range.
    """
    if start_port > max_port:
        raise ValueError("start_port must be <= max_port")
    for port in range(start_port, max_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"No free port found in range {start_port}-{max_port}")

