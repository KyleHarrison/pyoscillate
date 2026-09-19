# CLAUDE.md

## Project: Agentic Procedural Music and Sound Design with Pyo

This project's agentic music/sound-design behaviour is implemented as a Claude
Code skill:

```text
.claude/skills/pyo-music/SKILL.md
```

**Read that file to operate as this project's music/sound-design agent.**
It routes a natural-language musical or sonic request through two knowledge
layers and into working Pyo code:

```text
.claude/skills/pyo-music/
├── SKILL.md                          ← routing/operating layer, read first
└── references/
    ├── 00-navigation.md              ← music-composition knowledge (theory, genre, form, ...)
    ├── pyo-api-navigation.md         ← links synthesis concepts to pyo-api/ files
    ├── pyo-api/                      ← authoritative Pyo object documentation
    └── ...                           ← the rest of the music-composition reference library
```

This file (`CLAUDE.md`) intentionally stays short: it exists to point at
`SKILL.md`, not to duplicate its routing logic or the knowledge underneath
it.

## Foundational principle

**Do not map words directly to Pyo objects** ("dark" → `Lowpass`, "metallic"
→ `Resonx`, "ambient" → `Reverb`). A single perceptual description can have
many valid synthesis strategies, and one Pyo object can serve many different
musical purposes. Move through musical reasoning → sonic reasoning →
synthesis strategy → Pyo implementation, as `SKILL.md` describes — don't
collapse that chain early.

## Non-agentic project setup

Audio backend dependencies (see `README.md` for the full list and the
current Pyo API conceptual map):

```
brew install flac ffmpeg liblo libsndfile portaudio portmidi
```

When running Python from the CLI, use `uv run` (for example, `uv run python
script.py` or `uv run python -c "..."`) rather than invoking `python` directly.

Patches live in `src/pysynth/patches/`; each is a `build(...) -> Patch` /
`widget(...)` pair driven from the notebooks in `notebooks/`. `SKILL.md`
covers how to extend or reason about these.
