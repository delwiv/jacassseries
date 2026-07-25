from __future__ import annotations

import os
from importlib.util import find_spec
from typing import Optional

import numpy as np


def _cublas_lib_path() -> Optional[str]:
    try:
        spec = find_spec("nvidia.cublas")
        if spec is None or not spec.submodule_search_locations:
            return None
        pkg_path = next(iter(spec.submodule_search_locations))
        lib_path = os.path.join(pkg_path, "lib")
        if os.path.isdir(lib_path) and any(
            ".so" in f for f in os.listdir(lib_path)
        ):
            return lib_path
    except Exception:
        pass
    return None


def _cuda_available() -> bool:
    return _cublas_lib_path() is not None


def _pick_device(device: str) -> str:
    if device != "auto":
        return device
    return "cuda" if _cuda_available() else "cpu"


def _pick_compute_type(device: str, compute_type: str) -> str:
    if compute_type != "auto":
        return compute_type
    return "float16" if device == "cuda" else "int8"


class Transcriber:
    def __init__(
        self,
        model_size: str = "small",
        language: str = "fr",
        device: str = "auto",
        compute_type: str = "auto",
    ) -> None:
        self.model_size = model_size
        self.language = language
        self.device = device
        self.compute_type = compute_type
        self._model = None

    def load_model(self) -> None:
        if self._model is not None:
            return
        device = _pick_device(self.device)
        compute = _pick_compute_type(device, self.compute_type)
        print(f"[stt] loading {self.model_size} ({device}/{compute})...")
        from faster_whisper import WhisperModel

        self._model = WhisperModel(
            self.model_size,
            device=device,
            compute_type=compute,
        )
        print("[stt] model loaded")

    def reload(self) -> None:
        self._model = None
        self.load_model()

    def transcribe(self, audio: np.ndarray) -> str:
        self.load_model()
        segments, info = self._model.transcribe(
            audio,
            language=self.language,
            beam_size=5,
            condition_on_previous_text=False,
        )
        return " ".join(seg.text for seg in segments)
