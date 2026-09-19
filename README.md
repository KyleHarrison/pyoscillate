# Pyoscillate

Agentic DSP patches for Pyo, built for interactive experimentation in Jupyter notebooks.

Pyoscillate is a small, notebook-first toolkit for assembling reusable audio voices into a live modular performance environment. The core idea is simple: build synth components as expressive, tweakable building blocks, then audition them in real time from notebook cells while a shared timing system keeps everything in sync.

This project is meant for a workflow where sound design and patching feel more like a live instrument than a static script. You prototype a voice, tune its controls, route it into a larger arrangement, and iterate quickly without leaving the notebook.

## What this project does

Pyoscillate helps you:

- design custom Pyo-based synth voices and effects
- compose systems of patches that share a tempo and timing grid
- experiment interactively with controls in a notebook UI
- prototyping modular-synth ideas as live, audible building blocks
- save and reload patch states for quick recall and iteration

The emphasis is on rapid exploration: small patches, live auditioning, fast tuning, and compositional experimentation in context.

## Core ideas

### Modular voice design

Each patch behaves like a small module in a larger synth rig: it has its own sound, its own motion, and its own controllable parameters, while still fitting into a shared system.

### Shared timing

Rather than treating every patch as an isolated loop, the system is designed to let multiple voices lock into a common rhythmic reference. That makes layered textures feel coherent even when each element has its own character.

### Interactive prototyping

The notebook is the main interface: patch cells can be run, adjusted, stopped, and replayed in place. This makes the workflow feel closer to a live performance tool than a one-off script.

### Preset-driven exploration

A patch rig can be tuned, saved, and reloaded as a whole. That keeps experimentation fluid while preserving interesting combinations of modulation, timing, and tone.

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

Open the notebook environment and start the live rig:

```bash
jupyter lab
```

Then run the notebook that initializes the audio server, sets up the shared timing, and launches the patch rack. The intended experience is a live studio setup where patch cells are rerun as you shape the sound.

## Typical workflow

A typical session looks like this:

1. start the audio engine
2. create a shared tempo and timing context
3. load a notebook rig or build one from small patch modules
4. audition each voice in context
5. tweak controls and rerun cells immediately
6. save useful combinations as presets for later recall

This is the heart of the project: not just writing DSP code, but iterating on a living system in real time.

## Why it exists

Pyoscillate is for building musical systems with a procedural, agentic mindset: small, composable pieces of DSP that can be tested, tuned, and combined into something larger. It is a tool for exploring how synth components behave when they are treated as interactive building blocks rather than fixed one-off patches.

## License

This project is under active development and is intended as a creative coding environment for experimentation with Pyo, DSP, and live notebook-based sound design.

