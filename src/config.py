from __future__ import annotations

import os
import re
import tomllib
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


CONFIG_DIR = Path.home() / ".config" / "jacasseries"
CONFIG_PATH = CONFIG_DIR / "config.toml"

_env_pattern = re.compile(r"\$\{([^}]+)\}")


def _resolve_env(value: str) -> str:
    def _replace(m: re.Match) -> str:
        return os.environ.get(m.group(1), "")
    return _env_pattern.sub(_replace, value)


DEFAULT_CONFIG = {
    "api": {
        "url": "http://localhost:8080",
        "key": "",
    },
    "llm": {
        "model": "",
    },
    "stt": {
        "language": "fr",
        "model_size": "small",
        "device": "auto",
        "compute_type": "auto",
    },
    "tts": {
        "voice": "",
    },
    "audio": {
        "microphone": "",
    },
    "general": {
        "keyboard_shortcut": "",
        "silence_timeout": 2.0,
    },
}


@dataclass
class Config:
    api_url: str = "http://localhost:8080"
    api_key: str = ""
    llm_model: str = ""
    stt_language: str = "fr"
    stt_model_size: str = "small"
    stt_device: str = "auto"
    stt_compute_type: str = "auto"
    tts_voice: str = ""
    microphone: str = ""
    keyboard_shortcut: str = ""
    silence_timeout: float = 2.0

    @classmethod
    def load(cls) -> Config:
        if not CONFIG_PATH.exists():
            return cls()
        raw = CONFIG_PATH.read_text()
        data = tomllib.loads(raw)
        cfg = cls()
        cfg.api_url = _resolve_env(data.get("api", {}).get("url", cfg.api_url))
        cfg.api_key = _resolve_env(data.get("api", {}).get("key", cfg.api_key))
        cfg.llm_model = _resolve_env(data.get("llm", {}).get("model", cfg.llm_model))
        cfg.stt_language = _resolve_env(data.get("stt", {}).get("language", cfg.stt_language))
        cfg.stt_model_size = _resolve_env(data.get("stt", {}).get("model_size", cfg.stt_model_size))
        cfg.stt_device = _resolve_env(data.get("stt", {}).get("device", cfg.stt_device))
        cfg.stt_compute_type = _resolve_env(data.get("stt", {}).get("compute_type", cfg.stt_compute_type))
        cfg.tts_voice = _resolve_env(data.get("tts", {}).get("voice", cfg.tts_voice))
        cfg.microphone = _resolve_env(data.get("audio", {}).get("microphone", cfg.microphone))
        cfg.keyboard_shortcut = _resolve_env(data.get("general", {}).get("keyboard_shortcut", cfg.keyboard_shortcut))
        cfg.silence_timeout = float(data.get("general", {}).get("silence_timeout", cfg.silence_timeout))
        return cfg

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        lines = [
            "[api]",
            f'url = "{self.api_url}"',
            f'key = "{self.api_key}"',
            "",
            "[llm]",
            f'model = "{self.llm_model}"',
            "",
            "[stt]",
            f'language = "{self.stt_language}"',
            f'model_size = "{self.stt_model_size}"',
            f'device = "{self.stt_device}"',
            f'compute_type = "{self.stt_compute_type}"',
            "",
            "[tts]",
            f'voice = "{self.tts_voice}"',
            "",
            "[audio]",
            f'microphone = "{self.microphone}"',
            "",
            "[general]",
            f'keyboard_shortcut = "{self.keyboard_shortcut}"',
            f'silence_timeout = "{self.silence_timeout}"',
        ]
        CONFIG_PATH.write_text("\n".join(lines) + "\n")
