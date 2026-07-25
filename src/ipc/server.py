from __future__ import annotations

import json
import os
import socket
import threading
from pathlib import Path
from typing import Optional


SOCKET_DIR = Path.home() / ".local" / "state" / "jacasseries"
SOCKET_PATH = SOCKET_DIR / "jacasseries.sock"


class IPCServer:
    def __init__(self) -> None:
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self.on_command: Optional[callable] = None

    def start(self) -> None:
        SOCKET_DIR.mkdir(parents=True, exist_ok=True)
        if SOCKET_PATH.exists():
            SOCKET_PATH.unlink()
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        print(f"[ipc] server listening at {SOCKET_PATH}")

    def stop(self) -> None:
        self._running = False
        if SOCKET_PATH.exists():
            try:
                SOCKET_PATH.unlink()
            except OSError:
                pass

    def _run(self) -> None:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
            try:
                server.bind(str(SOCKET_PATH))
            except OSError:
                print("[ipc] bind failed")
                return
            server.settimeout(0.5)
            server.listen(1)
            while self._running:
                try:
                    conn, _ = server.accept()
                    data = conn.recv(4096)
                    if not data:
                        conn.close()
                        continue
                    cmd = json.loads(data.decode())
                    if self.on_command:
                        self.on_command(cmd)
                    conn.close()
                except (json.JSONDecodeError, OSError):
                    continue
