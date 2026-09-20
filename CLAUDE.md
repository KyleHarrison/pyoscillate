# CLAUDE.md

## Project: Agentic Procedural Music and Sound Design with Pyo

This project has three entry points, each with a distinct job:

- [SKILL.md](SKILL.md) — project-level routing and top-level entry point
- [.claude/skills/music-theory/SKILL.md](.claude/skills/music-theory/SKILL.md) — composition and music-theory reasoning
- [.claude/skills/pyo-music/SKILL.md](.claude/skills/pyo-music/SKILL.md) — sonic/perceptual translation before implementation

## Project-level routing

For a request involving a real patch, a rack, or a new project, follow this order:

1. Determine whether the task is purely musical, sonic-to-DSP translation, or implementation/project scaffolding.
2. If it is musical theory/composition-only, read [.claude/skills/music-theory/SKILL.md](.claude/skills/music-theory/SKILL.md).
3. If it is sound design or synthesis translation, read [.claude/skills/pyo-music/SKILL.md](.claude/skills/pyo-music/SKILL.md).
4. If it is project architecture, rack creation, `PatchDef` structure, or new project scaffolding, use this file and its workflow below.

This file is the correct place for concrete implementation and project-flow rules. The music skill remains a conceptual layer; it does not own the scaffolding or runtime architecture.

## Foundational principle

**Do not map words directly to Pyo objects** ("dark" → `Lowpass`, "metallic"
→ `Resonx`, "ambient" → `Reverb`). A single perceptual description can have
many valid synthesis strategies, and one Pyo object can serve many different
musical purposes. Move through musical reasoning → sonic reasoning →
synthesis strategy → Pyo implementation, as the skill chain describes — don't
collapse that chain early.

## New project workflow

When the user asks for a new project named `{project_name}` (a whole new Flet
app + patch rack, not a single patch edit), use this workflow in order:

1. **Ground the request.** Start with the musical and sonic brief, then translate it through the music and pyo-music skills before creating files.
2. **Choose the project layout.** Create the project package under `src/flet/{project_name}/` and the rack under `src/pyoscillate/projects/{project_name}/` when a new app/rack is required.
3. **Reuse or extend existing patch families first.** Search the nearest patch family before creating a new module. Extend an existing family or builder when possible.
4. **Implement the patch set.** Use the real patch modules under `src/pyoscillate/patches/` and the canonical runtime conventions there as the implementation source of truth.
5. **Wire the rack.** Put the `PATCH_DEFS` list in the project rack module and keep the app layer thin.
6. **Add README and notebook support.** Document the musical brief and concept-to-patch mapping; create the notebook preset structure and patch widgets when relevant.
7. **Validate the runtime contract.** Keep the patch graph and runtime state aligned with the project's patch architecture rules.

This is a project-level workflow, not a music-skill workflow. It lives here so it remains discoverable to agents and to future project creation tasks.

## Non-agentic project setup

Audio backend dependencies (see `README.md` for the full list and the
current Pyo API conceptual map):

```
brew install flac ffmpeg liblo libsndfile portaudio portmidi
```

When running Python from the CLI, use `uv run` (for example, `uv run python
script.py` or `uv run python -c "..."`) rather than invoking `python` directly.

To run linting instead of: `source .venv/bin/activate && ruff check src` just use `uv run ruff check src`

Patches live in `src/pyoscillate/patches/`; each is a `build(...) -> Patch` /
`widget(...)` pair driven from the notebooks in `notebooks/`. The actual
implementation and runtime discipline live in the project patch docs and the real
modules under that folder.

## Implementation authority

The authoritative implementation references are:

- `src/pyoscillate/patches/base.py` — shared patch lifecycle and runtime safety
- `src/pyoscillate/patches/widgets.py` — `SliderSpec` and UI conventions
- `src/pyoscillate/patches/deep_house/kick.py` — canonical profile-based family pattern
- `src/pyoscillate/projects/*/rack.py` — rack wiring for concrete projects

Those are the actual sources of truth for the patch architecture. The skill files should route into them and explain the musical reasoning, not duplicate their implementation contracts.
