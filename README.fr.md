> **[🇬🇧 English version](README.md)**

# jacasseries

Interface vocale pour LLM — discute avec ton IA comme tu bavarderais avec quelqu'un.

## Vue d'ensemble

jacasseries est une interface vocale desktop pour dialoguer avec un grand modèle
de langage. La reconnaissance vocale (STT) et la synthèse vocale (TTS) sont
100% locales (faster-whisper + Piper TTS). Le LLM peut être distant (toute API
compatible OpenAI, ex. llama.cpp).

Le nom vient du français *jacasser* — bavarder comme une pie.

## Fonctionnalités

- Bouton flottant (FAB) — toujours au-dessus, coloré selon l'état
- Mode dictée — parle pour écrire dans n'importe quel champ de texte
- STT temps réel via faster-whisper (CUDA optionnel)
- TTS streaming — l'audio commence avant la fin de la génération LLM
- Arrêt automatique au silence (timeout configurable) pour la dictée
- Flags CLI + socket IPC pour les raccourcis Wayland (`--dicter`, `--jacasser`, `--reset`)
- Configuration via interface (URL, clé, modèle, voix, micro)
- Historique de conversation
- Licence MIT, aucun service cloud pour la voix

## Pipeline

### Mode discussion

```
[Raccourci / Clic] → [Audio Capture] → [faster-whisper STT]
                              ↓
                      [LLM API (OpenAI)]
                              ↓
               [Découpage en phrases] → [Piper TTS] → [Audio]
```

États : `idle → enregistrement → transcription → llm → tts → idle`

### Mode dictée

```
[Raccourci / Clic] → [Audio Capture] → [faster-whisper STT]
                              ↓
                       [Presse-papier + wtype]
                              ↓
                    [Texte injecté dans le champ actif]
```

États : `idle → enregistrement → transcription → (texte injecté) → idle`

## Prérequis

- Python ≥ 3.11
- Linux (macOS/Windows prévu)
- GPU CUDA recommandée mais optionnelle (AMD/Intel via Vulkan prévu)
- `wtype` — nécessaire pour la dictée (tout compositeur Wayland)
- `~/.local/bin` dans le `PATH` — pour la commande `jacasseries`

### X11 vs Wayland

| Fonctionnalité | X11 | Wayland |
|------|:---:|:-------:|
| Raccourci clavier (`pynput`) | Oui | Non (utiliser le compositeur) |
| Injection texte dictée (`pynput`) | Oui | Non |
| Injection texte dictée (`wtype`) | Non | Oui |

## Installation

### Dépendances système

```bash
# Mode dictée (Wayland)
sudo apt install wtype        # Debian/Ubuntu
sudo pacman -S wtype           # Arch
sudo dnf install wtype         # Fedora
```

### Package Python

#### pipx (recommandé — Arch, compatible PEP 668)

```bash
sudo pacman -S python-pipx    # Arch
pipx install /chemin/vers/jacasseries
```

#### pip (Debian, Fedora, macOS)

```bash
git clone https://github.com/your-username/jacasseries.git
cd jacasseries
pip install --user -e .
```

La commande `jacasseries` est disponible dans `~/.local/bin/jacasseries`.

## Configuration

Premier lancement → création de `~/.config/jacasseries/config.toml`.
Édition via l'interface (clic droit FAB → Configuration) ou directement.

| Clé | Défaut | Description |
|-----|--------|-------------|
| `api.url` | `http://localhost:8080` | URL du serveur LLM |
| `api.key` | `""` | Clé API (`${ENV_VAR}` supporté) |
| `llm.model` | premier de `/v1/models` | Modèle LLM |
| `stt.language` | `fr` | Langue STT |
| `stt.model_size` | `small` | Taille du modèle Whisper |
| `tts.voice` | `fr_FR-siwis-medium` | Voix Piper |
| `silence_timeout` | `2.0` | Délai avant arrêt auto (secondes) |

Le prompt système est en français (texte brut, pas de markdown, pas d'émojis).

## Utilisation

```bash
jacasseries             # lancement en idle
jacasseries --dicter    # démarre un enregistrement en dictée
jacasseries --jacasser  # démarre une discussion
jacasseries --reset     # réinitialise l'historique
```

Hot start : si l'app tourne déjà, la commande est envoyée via le socket IPC.

### Mode discussion

- **Clic** FAB → start/stop enregistrement → STT → LLM → TTS → lecture
- **Clic droit** → Nouvelle discussion / Config / Mode dictée / Quitter
- **Appui long** → réinitialiser la discussion

### Mode dictée

Activation via le menu clic droit → "Mode dictée". L'icône FAB devient ⌨.

- **Clic** FAB → enregistrement → parle → silence auto-stop → texte tapé
- Texte aussi copié dans le presse-papier (Ctrl+V)

### Configuration du compositeur Wayland

| Compositeur | Configuration |
|-------------|---------------|
| Sway | `bindsym $mod+d exec jacasseries --dicter` |
| Hyprland | `bind = $mod, D, exec, jacasseries --dicter` |
| River | `riverctl map normal Super+Z spawn "jacasseries --dicter"` |
| KDE | Paramètres système → Raccourcis → `jacasseries --dicter` |
| GNOME | Extensions + Paramètres → Raccourcis → `jacasseries --dicter` |

## Structure du projet

Voir [README.md](README.md) (section Project Structure).

## Feuille de route

- [x] Pipeline core : enregistrement → STT → LLM → TTS → lecture
- [x] Mode dictée avec arrêt au silence et injection de texte
- [x] Socket IPC + flags CLI (`--dicter`, `--jacasser`, `--reset`)
- [x] Package installable via pip/pipx commande `jacasseries` dans le PATH
- [ ] Paquet AUR (et autres distros)
- [ ] Détection matérielle (CUDA / Vulkan pour AMD/Intel)
- [ ] openWakeWord pour interruption mains-libres
- [ ] Streaming des transcriptions partielles vers le LLM
- [ ] Support Windows / macOS
- [ ] Animation du spectre audio sur le FAB
- [ ] Gestion du contexte de conversation

## Licence

MIT — voir [LICENCE](LICENCE).
