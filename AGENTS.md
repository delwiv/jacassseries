# jacasseries — Voice Interface for LLM

**jacasseries** — from the cry of the magpie (jacasser), which also means to chatter.
Project: a voice interface to chat with an LLM, like you'd chat with someone.

## Philosophy

- **Prose coding**, not vibe coding. Every line is thought through.
- **DO NOT fill in the blanks.** If an instruction is ambiguous, ask for clarification. Do not invent decisions.
- Architecture first, code afterwards.
- Short iterations, solid foundations.

## License

MIT — do what you want, credit the original author.

## General Architecture

```
┌──────────────────────────────────────────────────────────┐
│                      jacasseries                          │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  [OS Signal / Keyboard Shortcut / IPC]                    │
│         │                                                 │
│         ▼                                                 │
│  [Audio Capture] ──buffers 200ms──► [faster-whisper]      │
│  (sounddevice)       streaming        (CUDA, local)       │
│         │                                                 │
│         │          ◄── partial transcriptions ──          │
│         ▼                                                 │
│  [Voice Activity Detection]                               │
│  (EnergyVAD)                                              │
│         │                                                 │
│         ▼                                                 │
│  [LLM API] (llama.cpp server, OpenAI-compatible, distant) │
│         │  SSE streaming                                  │
│         ▼                                                 │
│  [Piper TTS] ──► [Audio Output]                           │
│  (local, CUDA)     (sounddevice)                          │
│                                                           │
│  [Floating Widget] — real-time state indicator            │
│  [System Tray] — minimise to tray                         │
│  [Configuration] — URL, Key, Model, Voice                 │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

## Pipeline (data flow)

1. **idle** — mic off, FAB visible, grey mic icon
2. **recording** — user presses (click/shortcut), audio buffers sent to faster-whisper continuously. Partial transcriptions displayed. FAB → red, active mic icon
3. **transcribing** — recording ends, final transcription produced
4. **llm** — transcription sent to LLM via streaming API. FAB → blue/thinking
5. **tts** — LLM response streamed to Piper TTS chunk by chunk, audio played. FAB → green, speaker icon
6. **dictation** — transcription injected directly into focused field (skip LLM + TTS)
7. **back to idle** — ready for next interaction

## FAB Widget States

| State | Color | Icon | Behaviour |
|-------|-------|------|-----------|
| idle | Grey | 🎤 | Click = start recording |
| recording | Red | 🎤 (animated) | Click = stop recording |
| transcribing | Orange | ✏️ | Transient |
| llm | Blue | 🤖 | Streaming LLM |
| tts | Green | 🔊 | Audio playing. Click = interrupt TTS |

Future: audio spectrum animation around the button during recording.

## Tech Stack

| Layer | Technology | Reason |
|-------|-----------|--------|
| Language | Python 3.11+ | Rich ecosystem, bindings everywhere |
| UI | PySide6 | LGPL, frameless, system tray, cross-platform, mature |
| Audio I/O | sounddevice | Low latency, streaming, multi-platform |
| STT | faster-whisper | Native Python, CUDA, 4x faster than Whisper |
| VAD | EnergyVAD (custom) | RMS-based, zero dependencies, integrated |
| TTS | Piper TTS | Local, fast, multilingual, French voices |
| LLM Client | httpx + SSE | Streaming, OpenAI-compatible API |
| Text Injection | wtype | Wayland-native keyboard simulation |
| IPC | Unix socket | CLI flags → daemon communication |
| Keyword Spotting | openWakeWord (future) | Lightweight, CPU only, dedicated |
| Config | TOML | Simple, readable |

## Audio Capture: streaming to STT

- 200ms sliding buffer, sent to faster-whisper continuously.
- Whisper produces partial transcriptions that are refined.
- Currently: wait for recording end before sending to LLM.
- Future: streaming partial transcriptions to LLM for early response.

## Dictation Mode

- Speak → silence auto-stop (EnergyVAD, configurable timeout) → transcribe
- Text copied to clipboard AND injected into focused field via `wtype`
- FAB icon switches to ⌨

## IPC & CLI Flags

- Unix socket at `~/.local/state/jacasseries/jacasseries.sock`
- Hot start: app already running → command sent via socket → exit
- Cold start: app launches, buffers command, executes after model preload
- Flags: `--dicter`, `--jacasser`, `--reset`

## Configuration

Config window with:

- **API URL** : llama.cpp server URL (or any OpenAI-compatible server)
- **API Key** : optional, depending on server config
- **LLM Model** : selector based on `GET /v1/models`
- **STT Language** : French, English, auto
- **TTS Voice** : selection from available Piper voices
- **Keyboard shortcut** : deprecated under Wayland (use compositor bindings + IPC)
- **Microphone** : input device selection

Storage: `~/.config/jacasseries/config.toml`

## Project Structure

```
jacasseries/
├── AGENTS.md
├── LICENSE
├── pyproject.toml
├── README.md
├── README.fr.md
├── src/
│   ├── main.py                  Entry point + CLI args
│   ├── app.py                   PySide6 application
│   ├── config.py                TOML config management
│   ├── audio/
│   │   ├── capture.py           sounddevice → buffers
│   │   ├── output.py            sounddevice playback
│   │   └── vad.py               EnergyVAD (silence detection)
│   ├── stt/
│   │   └── transcriber.py       faster-whisper wrapper
│   ├── llm/
│   │   └── client.py            OpenAI-compatible API client
│   ├── tts/
│   │   └── synthesizer.py       Piper TTS wrapper
│   ├── input/
│   │   └── injector.py          wtype text injection
│   ├── ipc/
│   │   ├── server.py            Unix socket server
│   │   └── client.py            Unix socket client
│   ├── pipeline/
│   │   ├── orchestrator.py      State machine + mode
│   │   └── streamer.py          TTS streaming engine
│   ├── ui/
│   │   ├── fab.py               Floating action button
│   │   ├── tray.py              System tray
│   │   └── config_window.py     Configuration dialog
│   └── keyword/
│       └── spotter.py           Global shortcut (X11 pynput)
├── tests/
│   └── ...
└── resources/
    ├── icons/
    └── styles/
```

## Roadmap (phases)

### Phase 1 — skeleton
- [x] Project structure, pyproject.toml, dependencies
- [x] TOML config (read/write)
- [x] Audio capture (sounddevice, buffers)
- [x] FAB widget (PySide6, frameless, always-on-top)
- [x] Pipeline orchestrator (idle/recording/llm/tts states)

### Phase 2 — STT + LLM
- [x] faster-whisper integration (CUDA, streaming buffers)
- [x] LLM client (OpenAI-compatible API, SSE)
- [x] Full loop: recording → transcription → LLM → text display

### Phase 3 — TTS + playback
- [x] Piper TTS integration
- [x] Audio output
- [x] Full audio loop: recording → STT → LLM → TTS → speaker
- [x] Interruption by re-click

### Phase 4 — Dictation + IPC
- [x] Dictation mode (silence auto-stop, clipboard, wtype injection)
- [x] IPC socket + CLI flags (`--dicter`, `--jacasser`, `--reset`)
- [x] Packaging (pip/pipx installable)

### Phase 5 — UI complete
- [x] Icons and colours per state
- [x] Configuration window
- [x] System tray + minimisation
- [ ] Audio spectrum on FAB

### Phase 6 — Polish v1
- [x] Error handling (network, GPU, mic)
- [x] Logs
- [ ] AUR package (and other distro packages)
- [ ] Tests

### Phase 7+ — Improvements
- [ ] openWakeWord keyword spotting + interruption
- [ ] Natural VAD during recording (auto-stop on silence)
- [ ] Streaming partial transcriptions to LLM
- [ ] Streaming early TTS tokens before LLM finishes
- [ ] Windows / macOS support
- [ ] Conversational context (history)

## Code Conventions

- Type hints everywhere
- Single-responsibility classes
- Async where possible (httpx, audio processing)
- DRY — factorise without over-engineering
- Tests per module
- `ruff` for formatting, `mypy` for typing
- Docstrings only for public API (don't comment the obvious)

## Key dependencies (pyproject.toml)

```toml
[project]
name = "jacasseries"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "PySide6>=6.7",
    "sounddevice>=0.5",
    "faster-whisper>=1.1",
    "piper-tts>=1.2",
    "httpx[sse]>=0.27",
    "qtawesome>=1.4",
    "pynput>=1.7",
]

[project.optional-dependencies]
keyword = ["openwakeword"]
```

## Final Notes

- The LLM is an external service (llama.cpp server, or any OpenAI-compatible server).
- STT and TTS are 100% local.
- The interface should be discreet — small, semi-transparent FAB that blends in.
- Nothing is sent to the cloud except LLM requests (via the configured API).
- Latency is enemy number one — every millisecond counts.
- No edge computing, no internet dependency for voice.
