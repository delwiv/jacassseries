from __future__ import annotations

from enum import Enum, auto
from typing import Optional


class State(Enum):
    IDLE = auto()
    RECORDING = auto()
    TRANSCRIBING = auto()
    LLM = auto()
    TTS = auto()


class Mode(Enum):
    CONVERSATION = auto()
    DICTATION = auto()


class Orchestrator:
    def __init__(self) -> None:
        self._state = State.IDLE
        self._mode = Mode.CONVERSATION
        self._listeners: list[callable] = []
        self._mode_listeners: list[callable] = []
        self.on_transcription_ready: Optional[callable] = None
        self.on_llm_token: Optional[callable] = None
        self.on_llm_ready: Optional[callable] = None

    @property
    def state(self) -> State:
        return self._state

    @property
    def mode(self) -> Mode:
        return self._mode

    def set_mode(self, mode: Mode) -> None:
        if mode == self._mode:
            return
        self._mode = mode
        for listener in self._mode_listeners:
            listener(mode)

    def on_state_change(self, listener: callable) -> None:
        self._listeners.append(listener)

    def on_mode_change(self, listener: callable) -> None:
        self._mode_listeners.append(listener)

    def _set_state(self, new_state: State) -> None:
        if new_state == self._state:
            return
        old_state = self._state
        self._state = new_state
        print(f"[orchestrator] {old_state.name} -> {new_state.name}")
        for listener in self._listeners:
            listener(new_state)

    def start_recording(self) -> None:
        if self._state == State.TTS:
            self._set_state(State.IDLE)
        self._set_state(State.RECORDING)

    def stop_recording(self) -> None:
        if self._state == State.RECORDING:
            self._set_state(State.TRANSCRIBING)

    def transcription_done(self, text: str) -> None:
        if self._state != State.TRANSCRIBING:
            return
        if self._mode == Mode.DICTATION:
            self._set_state(State.IDLE)
        else:
            self._set_state(State.LLM)
        if self.on_transcription_ready:
            self.on_transcription_ready(text)

    def llm_done(self, text: str) -> None:
        if self._state != State.LLM:
            return
        self._set_state(State.TTS)
        if self.on_llm_ready:
            self.on_llm_ready(text)

    def tts_done(self) -> None:
        if self._state == State.TTS:
            self._set_state(State.IDLE)

    def interrupt(self) -> None:
        if self._state != State.IDLE:
            self._set_state(State.IDLE)
