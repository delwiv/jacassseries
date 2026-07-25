from __future__ import annotations

import subprocess
import shutil


class TextInjector:
    def __init__(self) -> None:
        self._wtype = shutil.which("wtype")

    def inject(self, text: str) -> None:
        if self._wtype is None:
            print("[injector] wtype not found — install it: sudo apt install wtype")
            return
        subprocess.run([self._wtype, text], check=True)
