# jacasseries

Voice interface for LLM — talk to your AI like you'd chat with a friend.

## Overview

jacasseries is a desktop voice interface for conversing with a large language
model. Speech-to-text and text-to-speech run 100% locally (faster-whisper +
Piper TTS). The LLM can be remote (any OpenAI-compatible API, e.g. llama.cpp).

The name comes from the French *jacasser* — to chatter like a magpie.

## Features

- Push-to-talk floating button (FAB) — always-on-top, draggable, color-coded
- Dictation mode — speak to type into any focused input field
- Real-time STT via faster-whisper (CUDA optional)
- Streaming TTS — audio starts before the LLM finishes generating
- Silence-based auto-stop (configurable timeout) for dictation
- Global keyboard shortcut (configurable via UI)
- System tray minimisation
- Configuration UI (API URL/key, model, voice, microphone, shortcut)
- Conversation history across turns
- MIT license, no cloud dependencies for voice

## Pipeline

### Conversation mode

```
[Keyboard Shortcut / Click] → [Audio Capture] → [faster-whisper STT]
                                     ↓
                             [LLM API (OpenAI-compatible, SSE)]
                                     ↓
                           [Sentence splitter] → [Piper TTS] → [Audio Output]
```

States: `idle → recording → transcribing → llm → tts → idle`

### Dictation mode

```
[Keyboard Shortcut / Click] → [Audio Capture] → [faster-whisper STT]
                                     ↓
                              [Clipboard + wtype/pynput]
                                     ↓
                              [Text injected into focused field]
```

States: `idle → recording → transcribing → (text injected) → idle`

## Requirements

- Python ≥ 3.11
- Linux (macOS/Windows support planned)
- CUDA-capable GPU recommended but optional (AMD/Intel via Vulkan planned)
- `wtype` — required for dictation mode on **Wayland** (e.g. Sway)

### X11 vs Wayland

| Feature | X11 | Wayland |
|---------|:---:|:-------:|
| Keyboard shortcut (`pynput`) | Yes | No (use desktop WM binding) |
| Dictation text injection (`pynput`) | Yes | No |
| Dictation text injection (`wtype`) | No | Yes |

Under Wayland, jacasseries relies on your window manager for global shortcuts
(e.g. `bindsym $mod+r exec jacasseries`) and on `wtype` for text injection in
dictation mode. Future IPC support will unify the experience.

## Installation

### System dependencies

```bash
# Dictation mode on Wayland
sudo apt install wtype          # Debian/Ubuntu
sudo pacman -S wtype             # Arch
sudo dnf install wtype           # Fedora
```

No additional configuration needed — `wtype` works out of the box under Wayland.

### Python package

```bash
git clone https://github.com/your-username/jacasseries.git
cd jacasseries
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

For keyword-spotting support (future feature):

```bash
pip install -e ".[keyword]"
```

## Configuration

First launch creates `~/.config/jacasseries/config.toml`.
Edit through the GUI (right-click FAB → Config) or directly in the file.

| Key                | Default                     | Description                        |
|--------------------|-----------------------------|------------------------------------|
| `api.url`          | `http://localhost:8080`     | LLM server URL                     |
| `api.key`          | `""`                        | API key (`${ENV_VAR}` supported)   |
| `llm.model`        | first from `/v1/models`     | Model to use                       |
| `stt.language`     | `fr`                        | STT language                       |
| `stt.model_size`   | `small`                     | Whisper model size                 |
| `tts.voice`        | `fr_FR-siwis-medium`        | Piper voice                        |
| `silence_timeout`  | `2.0`                       | Auto-stop silence (seconds)       |

System prompt (French) is hardcoded for now — plain text, no markdown, no emojis.

## Usage

```bash
python -m jacasseries
```

### Conversation mode (default)

- **Click** the FAB → start / stop recording → STT → LLM → TTS → playback
- **Right-click** → New discussion / Config / Dictation mode / Quit
- **Long-press** the FAB → reset conversation
- **Keyboard shortcut** (if configured) → toggle recording

### Dictation mode

Toggle via right-click menu → "Mode dictée". The FAB icon changes to ⌨.

- **Click** the FAB → start recording → speak → silence auto-stop → text typed
- Text is also copied to clipboard for manual paste (Ctrl+V)
- Use for: dictating prompts, filling forms, writing without the keyboard

## Project Structure

```
src/
├── main.py              Entry point
├── app.py               Application (wires all components)
├── config.py            TOML configuration manager
├── audio/
│   ├── capture.py       Sounddevice input streaming
│   ├── output.py        Sounddevice playback
│   └── vad.py           Energy-based VAD (silence auto-stop)
├── stt/
│   └── transcriber.py   faster-whisper wrapper
├── llm/
│   └── client.py        OpenAI-compatible API client (SSE)
├── tts/
│   └── synthesizer.py   Piper TTS wrapper
├── input/
│   └── injector.py      Text injection (wtype/pynput)
├── pipeline/
│   ├── orchestrator.py  State machine + mode (conversation/dictation)
│   └── streamer.py      Sentence-level TTS streaming engine
├── ui/
│   ├── fab.py           Floating action button
│   ├── tray.py          System tray icon
│   └── config_window.py Configuration dialog
└── keyword/
    └── spotter.py       Global keyboard shortcut (pynput)
```

## Roadmap

**Current (Phase 1-2):** Core pipeline working — record → STT → LLM → TTS → play.
Dictation mode with silence auto-stop and text injection.

**Upcoming:**
- Hardware detection (CUDA / Vulkan for AMD/Intel)
- IPC + CLI flags for Wayland-native keyboard control
- openWakeWord keyword spotting for hands-free interruption
- Streaming partial transcriptions to LLM
- Cross-platform support (Windows, macOS)
- Audio spectrum animation on FAB
- Conversation context management

## License

MIT — see [LICENCE](LICENCE).
