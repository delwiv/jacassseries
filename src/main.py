from __future__ import annotations

import argparse
import os
import signal
import sys

from PySide6.QtCore import QTimer

FLAG_MAP = {
    "dictate": {"mode": "dictation", "record": True},
    "dicter": {"mode": "dictation", "record": True},
    "discuss": {"mode": "conversation", "record": True},
    "jacasser": {"mode": "conversation", "record": True},
    "reset": {"reset": True},
}


def _setup_cuda() -> None:
    from src.stt.transcriber import _cublas_lib_path
    path = _cublas_lib_path()
    if not path:
        return
    import ctypes
    for fname in sorted(os.listdir(path)):
        if ".so" not in fname:
            continue
        try:
            ctypes.CDLL(os.path.join(path, fname))
        except OSError as e:
            print(f"[cuda] warning: could not load {fname}: {e}")


def _parse_args() -> dict | None:
    parser = argparse.ArgumentParser(description="jacasseries — voice interface for LLM")
    for flag, action in FLAG_MAP.items():
        parser.add_argument(f"--{flag}", action="store_true", help=action.get("cmd", str(action)))
    args = parser.parse_args()
    cmd = {}
    for flag, action in FLAG_MAP.items():
        if getattr(args, flag.replace("-", "_"), False):
            cmd.update(action)
    return cmd if cmd else None


def main() -> None:
    cmd = _parse_args()

    if cmd:
        from src.ipc.client import send_command
        if send_command(cmd):
            print(f"[ipc] sent command: {cmd}")
            return

    _setup_cuda()

    from src.app import JacasseriesApp

    app = JacasseriesApp(sys.argv, startup_cmd=cmd)

    signal.signal(signal.SIGINT, lambda *_: QTimer.singleShot(0, app.quit))

    app.run()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
