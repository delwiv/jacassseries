from __future__ import annotations

import numpy as np
from typing import Optional

CHUNK_DURATION = 0.2  # 200ms at 16kHz


class EnergyVAD:
    def __init__(self, threshold: float = 0.005, timeout: float = 2.0) -> None:
        self.threshold = threshold
        self.timeout = timeout
        self._silent_limit = max(1, int(timeout / CHUNK_DURATION))
        self._silent_count = 0
        self._speech_detected = False
        self.on_silence_timeout: Optional[callable] = None

    def reset(self) -> None:
        self._silent_count = 0
        self._speech_detected = False

    def set_timeout(self, timeout: float) -> None:
        self.timeout = timeout
        self._silent_limit = max(1, int(timeout / CHUNK_DURATION))

    def process(self, audio: np.ndarray) -> None:
        if audio.size == 0:
            return
        rms = np.sqrt(np.mean(audio.astype("float64") ** 2))
        speech = rms >= self.threshold
        if speech:
            self._speech_detected = True
            self._silent_count = 0
        elif self._speech_detected:
            self._silent_count += 1
            print(f"[vad] silent chunk #{self._silent_count}/{self._silent_limit}, rms={rms:.5f}")
            if self._silent_count >= self._silent_limit:
                print("[vad] >>> TIMEOUT FIRING <<<")
                if self.on_silence_timeout:
                    self.on_silence_timeout()
                self._silent_count = 0
                self._speech_detected = False
