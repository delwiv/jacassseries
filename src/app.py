from __future__ import annotations

import threading
import traceback
from typing import Optional

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from src.audio.capture import AudioCapture, SAMPLE_RATE
from src.audio.output import AudioOutput
from src.audio.vad import EnergyVAD
from src.config import Config
from src.input.injector import TextInjector
from src.llm.client import LLMClient
from src.pipeline.orchestrator import Mode, Orchestrator, State
from src.pipeline.streamer import TTSStreamer
from src.stt.transcriber import Transcriber
from src.tts.synthesizer import Synthesizer
from src.keyword.spotter import GlobalShortcut
from src.ui.config_window import ConfigWindow
from src.ui.fab import FAB
from src.ui.tray import SystemTray


class _MainThread(QObject):
    invoke = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.invoke.connect(lambda fn: fn())

_main = _MainThread()


def _run_in_thread(target, on_done=None, on_error=None, label=""):
    def wrapper():
        try:
            print(f"[thread:{label}] starting")
            result = target()
            print(f"[thread:{label}] done, result={repr(result)[:80]}")
            if on_done:
                _main.invoke.emit(lambda: on_done(result))
        except Exception as exc:
            print(f"[thread:{label}] EXCEPTION: {exc}")
            traceback.print_exc()
            if on_error:
                _main.invoke.emit(lambda err=exc: on_error(err))
    threading.Thread(target=wrapper, daemon=True).start()


class JacasseriesApp(QApplication):
    def __init__(self, argv: list[str]) -> None:
        super().__init__(argv)
        self.setApplicationName("jacasseries")
        self.setOrganizationName("jacasseries")
        self.setQuitOnLastWindowClosed(False)

        self.config = Config.load()
        self.orchestrator = Orchestrator()
        self.fab = FAB()
        self.tray = SystemTray()
        self.injector = TextInjector()
        self.vad = EnergyVAD(timeout=self.config.silence_timeout)
        self.audio = AudioCapture()
        self.transcriber = Transcriber(
            model_size=self.config.stt_model_size,
            language=self.config.stt_language,
            device=self.config.stt_device,
            compute_type=self.config.stt_compute_type,
        )
        self.llm = LLMClient(
            base_url=self.config.api_url,
            api_key=self.config.api_key,
            model=self.config.llm_model,
        )
        self.synthesizer = Synthesizer(voice=self.config.tts_voice or "fr_FR-siwis-medium")
        self.audio_out = AudioOutput()
        self.streamer = TTSStreamer(self.synthesizer, self.audio_out)
        self.shortcut = GlobalShortcut()
        self.shortcut.on_activate = self._on_shortcut
        self._connect_signals()

    def _connect_signals(self) -> None:
        self.fab.clicked.connect(self._on_fab_click)
        self.fab.long_pressed.connect(self._reset_discussion)
        self.fab.config_requested.connect(self._open_config)
        self.fab.reset_requested.connect(self._reset_discussion)
        self.fab.quit_requested.connect(self.quit)
        self.fab.mode_change_requested.connect(self._on_mode_change)
        self.orchestrator.on_state_change(self._on_state_change)
        self.orchestrator.on_mode_change(self._on_mode_from_orchestrator)
        self.orchestrator.on_transcription_ready = self._on_transcription_ready
        self.orchestrator.on_llm_token = self._on_llm_token
        self.orchestrator.on_llm_ready = self._on_llm_ready
        self.streamer.on_done = lambda: _main.invoke.emit(self._on_tts_done)
        self.streamer.on_error = lambda e: _main.invoke.emit(self.orchestrator.interrupt)
        self.tray.show_requested.connect(self._toggle_visible)
        self.tray.config_requested.connect(self._open_config)
        self.tray.quit_requested.connect(self.quit)
        self.tray.mode_change_requested.connect(self._on_mode_change)

    def _toggle_visible(self) -> None:
        if self.fab.isVisible():
            self.fab.hide()
        else:
            self.fab.show()

    def _open_config(self) -> None:
        dialog = ConfigWindow(self.config, llm_client=self.llm)
        if dialog.exec():
            self._reload_config()

    def _reload_config(self) -> None:
        self.llm.base_url = self.config.api_url
        self.llm.api_key = self.config.api_key
        self.llm.model = self.config.llm_model
        self.transcriber.model_size = self.config.stt_model_size
        self.transcriber.language = self.config.stt_language
        self.synthesizer = Synthesizer(
            voice=self.config.tts_voice or "fr_FR-siwis-medium"
        )
        self.streamer = TTSStreamer(self.synthesizer, self.audio_out)
        self.streamer.on_done = lambda: _main.invoke.emit(self._on_tts_done)
        self.streamer.on_error = lambda e: _main.invoke.emit(self.orchestrator.interrupt)
        self.streamer.start()
        if self.config.microphone:
            self.audio.device = int(self.config.microphone)
        self.shortcut.register(self.config.keyboard_shortcut)
        _run_in_thread(lambda: self._preload_models(), label="preload")
        print("[config] reloaded")

    def _reset_discussion(self) -> None:
        self.audio.on_buffer = None
        self.streamer.stop()
        self.audio.stop()
        self.orchestrator.interrupt()
        self.llm.reset()
        print("\n--- nouvelle discussion ---")

    def _on_state_change(self, state: State) -> None:
        print(f"[orchestrator] -> {state.name}")
        self.fab.state = state

    def _start_recording(self) -> None:
        self.audio.on_buffer = None
        self.orchestrator.start_recording()
        self.audio.start()
        if self.orchestrator.mode == Mode.DICTATION:
            self.vad.set_timeout(self.config.silence_timeout)
            self.vad.reset()
            self.vad.on_silence_timeout = lambda: _main.invoke.emit(self._on_vad_silence)
            self.audio.on_buffer = self.vad.process
            print(f"[vad] dictation mode, on_buffer set, timeout={self.config.silence_timeout}s")
        print("\n--- recording ---")

    def _stop_and_transcribe(self) -> None:
        self.audio.on_buffer = None
        audio = self.audio.stop()
        self.orchestrator.stop_recording()
        print(f"--- transcribed ({len(audio) / SAMPLE_RATE:.1f}s) ---")
        _run_in_thread(
            lambda: self.transcriber.transcribe(audio),
            on_done=self.orchestrator.transcription_done,
            on_error=lambda _: self.orchestrator.interrupt(),
            label="stt",
        )

    def _on_vad_silence(self) -> None:
        print(f"[vad] _on_vad_silence called, state={self.orchestrator.state.name}")
        if self.orchestrator.state == State.RECORDING:
            print("[vad] silence timeout, auto-stop")
            self._stop_and_transcribe()

    def _on_fab_click(self) -> None:
        current = self.orchestrator.state
        print(f"[fab] click, state={current.name}")
        if current in (State.IDLE, State.TTS):
            if current == State.TTS:
                self.streamer.stop()
            self._start_recording()
        elif current == State.RECORDING:
            self._stop_and_transcribe()
        else:
            self.audio.on_buffer = None
            self.audio.stop()
            self.streamer.stop()
            self.orchestrator.interrupt()
            print("\n--- interrupted ---")

    def _on_mode_change(self, mode: Mode) -> None:
        print(f"[mode] switching to {mode.name}")
        if mode != self.orchestrator.mode:
            self.audio.on_buffer = None
            self.orchestrator.interrupt()
            self.streamer.stop()
            self.audio.stop()
        self.orchestrator.set_mode(mode)
        self.fab.set_mode(mode)
        self.tray.set_mode(mode)

    def _on_mode_from_orchestrator(self, mode: Mode) -> None:
        self.fab.set_mode(mode)
        self.tray.set_mode(mode)

    def _on_transcription_ready(self, text: str) -> None:
        print(f"[pipe] transcription ready, text={repr(text[:120])}")
        if not text.strip():
            print("[pipe] empty transcription, back to idle")
            self.orchestrator.interrupt()
            return
        print(f">> {text}")
        if self.orchestrator.mode == Mode.DICTATION:
            print("--- dictation: injecting text ---")
            QApplication.clipboard().setText(text)
            print(f"[clipboard] text copied ({len(text)} chars)")
            _run_in_thread(
                lambda: self.injector.inject(text),
                label="inject",
            )
        else:
            print("--- llm ---")
            _run_in_thread(
                lambda: self.llm.send_message(text, on_token=self._on_llm_token),
                on_done=self.orchestrator.llm_done,
                on_error=lambda _: self.orchestrator.interrupt(),
                label="llm",
            )

    def _on_llm_token(self, token: str) -> None:
        if token:
            print(token, end="", flush=True)
            self.streamer.feed_token(token)

    def _on_llm_ready(self, text: str) -> None:
        print(f"\n--- done ({len(text)} chars) ---")
        self.streamer.flush()

    def _on_tts_done(self) -> None:
        self.orchestrator.tts_done()

    def _on_shortcut(self) -> None:
        _main.invoke.emit(lambda: self._on_fab_click())

    def run(self) -> None:
        self.fab.show()
        self.tray.show()
        self.streamer.start()
        self.shortcut.register(self.config.keyboard_shortcut)
        _run_in_thread(lambda: self._preload_models(), label="preload")

    def _preload_models(self) -> None:
        print("[preload] loading models...")
        self.transcriber.load_model()
        self.synthesizer.load_voice()
        print("[preload] ready")
