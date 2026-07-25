from __future__ import annotations

import queue
import threading
from typing import Optional

import numpy as np

from ..audio.output import AudioOutput
from ..tts.synthesizer import Synthesizer


class SentenceAccumulator:
    def __init__(self) -> None:
        self._buffer = ""

    def add(self, token: str) -> Optional[str]:
        self._buffer += token
        sentence, self._buffer = self._split(self._buffer)
        return sentence

    def flush(self) -> str:
        remaining = self._buffer
        self._buffer = ""
        return remaining

    def clear(self) -> None:
        self._buffer = ""

    @staticmethod
    def _split(text: str) -> tuple[str, str]:
        for i in range(len(text)):
            if text[i] in ".!?\u2026" and i + 1 < len(text) and text[i + 1].isspace():
                return text[: i + 1], text[i + 1 :]
            if text[i] in ".!?\u2026" and i + 1 == len(text):
                return text, ""
        return "", text


class TTSStreamer:
    def __init__(self, synthesizer: Synthesizer, audio_out: AudioOutput) -> None:
        self.synthesizer = synthesizer
        self.audio_out = audio_out
        self._accumulator = SentenceAccumulator()
        self._queue: queue.Queue[Optional[str]] = queue.Queue()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.on_done: Optional[callable] = None
        self.on_error: Optional[callable] = None

    def start(self) -> None:
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def feed_token(self, token: str) -> None:
        if self._stop_event.is_set():
            return
        sentence = self._accumulator.add(token)
        if sentence:
            self._queue.put(sentence)

    def flush(self) -> None:
        remaining = self._accumulator.flush()
        if remaining:
            self._queue.put(remaining)
        self._queue.put(None)

    def stop(self) -> None:
        self._stop_event.set()
        self._accumulator.clear()
        self._drain_queue()
        self.audio_out.stop()

    def _drain_queue(self) -> None:
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except queue.Empty:
                break

    def _worker(self) -> None:
        while not self._stop_event.is_set():
            try:
                item = self._queue.get(timeout=0.3)
            except queue.Empty:
                continue
            self._queue.task_done()

            if item is None or self._stop_event.is_set():
                if item is None and self.on_done:
                    self.on_done()
                continue

            try:
                audio = self.synthesizer.synthesize(item)
                if len(audio) > 0 and not self._stop_event.is_set():
                    self.audio_out.play(audio, samplerate=self.synthesizer.sample_rate)
            except Exception as e:
                import traceback
                traceback.print_exc()
                if self.on_error:
                    self.on_error(e)
                continue
