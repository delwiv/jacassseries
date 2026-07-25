from __future__ import annotations

import json
import socket

from .server import SOCKET_PATH


def send_command(cmd: dict) -> bool:
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(3)
            s.connect(str(SOCKET_PATH))
            s.sendall(json.dumps(cmd).encode())
        return True
    except (FileNotFoundError, ConnectionRefusedError, OSError):
        return False
