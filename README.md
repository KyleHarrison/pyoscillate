# Pyoscillate

Agentic DSP patches for Pyo, played live as a modular synthesizer through a Flet GUI.

Pyoscillate is a small toolkit for assembling reusable audio voices into a live modular performance environment. The core idea is simple: build synth components as expressive, tweakable building blocks, wire them into a rack, and play that rack in real time from a Flet app while a shared clock keeps everything in sync.

This project is meant for a workflow where sound design and patching feel more like a live instrument than a static script. You prototype a voice, expose its musical controls, route it into a rack alongside other voices, and shape the whole rig from the GUI's switches and sliders.

## What this project does

Pyoscillate helps you:

- design custom Pyo-based synth voices and effects
- compose racks of patches that share a tempo and timing grid
- perform and tweak those racks live in a Flet modular-synth GUI
- prototype modular-synth ideas as live, audible building blocks
- save and reload whole-rack presets for quick recall and iteration

The emphasis is on rapid exploration: small patches, live auditioning, fast tuning, and compositional experimentation in context.

## Core ideas

### Modular voice design

Each patch behaves like a small module in a larger synth rig: it has its own sound, its own motion, and its own controllable parameters, while still fitting into a shared system.

### Shared timing

Rather than treating every patch as an isolated loop, the system is designed to let multiple voices lock into a common rhythmic reference. That makes layered textures feel coherent even when each element has its own character.

### Flet rack GUI

The Flet app is the main interface. Each project defines a rack of `Patch` instances grouped by `GroupController` (in `src/pyoscillate/projects/{project}/rack.py`), and the shared app layer in `src/flet/base.py` renders every patch as a panel with an enable switch, musical parameter sliders, and a volume slider, all driving one shared rack, clock, and audio engine. Everything is wired statically: a rack holds its patches and groups as typed attributes, a `Param` object is the only handle to a setting (volume included), and group sliders (nestable, so an outer group can move inner ones) are `GroupControl`s that assign parameters directly.

### Preset-driven exploration

A rack can be tuned, saved, and reloaded as a whole from the GUI. Presets are JSON files saved from the GUI into each app's `presets/` folder (created on demand; none are committed), which keeps experimentation fluid while preserving interesting combinations of modulation, timing, and tone.

## Installation

### macOS dependencies

Install the required system libraries with Homebrew:

```bash
brew update
brew install flac ffmpeg liblo libsndfile portaudio portmidi
```

If you need to refresh an existing install, a common follow-up is:

```bash
brew reinstall flac
```

### uv setup

This project is intended to work cleanly with `uv`.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync --group dev
```

If you prefer a local environment explicitly:

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

## Quick start

Launch a rack from the project root. For the deep-house rack in a browser:

```bash
uv run flet run --web --port 8551 src/flet/deep_house/app.py
```

Open http://127.0.0.1:8551 (for example in the VS Code browser), start the audio engine, and switch patches on.

Other racks live alongside it under `src/flet/` (`forest_psytrance`, `lofi`, `slowed_reverb`, `psyambient`). Drop `--web --port ...` to open a rack as a desktop window instead.

## Build macOS dist

```bash
uv run flet pack main.py \
  --name FMSoundscape \
  --product-name "FM Soundscape" \
  --bundle-id com.kyleharrison.fmsoundscape \
  --yes
```

## Typical workflow

A typical session looks like this:

1. launch a project's Flet rack
2. start the audio engine and set the shared tempo
3. switch voices on and audition each one in context
4. shape each voice with its musical sliders while the rack plays
5. save useful combinations as presets for later recall
6. edit patch modules or the rack definition, then relaunch to hear the change

## Debugging patches

Play any single patch module on its own with `uv run flet run src/flet/patch/app.py -- <module> style=<name> [param=value ...]`, or render and measure one offline with `uv run python -m pyoscillate.analysis <module> --set name=value`. Both build the patch with a full `BuildContext` (tempo, clock, harmony), so a failing lifecycle stage shows up in isolation.

## Why it exists

Pyoscillate is for building musical systems with a procedural, agentic mindset: small, composable pieces of DSP that can be tested, tuned, and combined into something larger. It is a tool for exploring how synth components behave when they are treated as modules in an interactive rack rather than fixed one-off patches.

## License

This project is under active development and is intended as a creative coding environment for experimentation with Pyo, DSP, and live modular sound design through a Flet GUI.
