# AGENTS.md

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
4. If it is project architecture, rack creation, `Patch`/`GroupController` structure, or new project scaffolding, read [src/pyoscillate/projects/AGENTS.md](src/pyoscillate/projects/AGENTS.md) for the concrete new-project workflow.

This file is the correct place for routing and the foundational principle below; the concrete new-project workflow itself lives in [src/pyoscillate/projects/AGENTS.md](src/pyoscillate/projects/AGENTS.md). The music skill remains a conceptual layer; it does not own the scaffolding or runtime architecture.

## Foundational principle

**Do not map words directly to Pyo objects** ("dark" → `Lowpass`, "metallic"
→ `Resonx`, "ambient" → `Reverb`). A single perceptual description can have
many valid synthesis strategies, and one Pyo object can serve many different
musical purposes. Move through musical reasoning → sonic reasoning →
synthesis strategy → Pyo implementation, as the skill chain describes — don't
collapse that chain early.

## Non-agentic project setup

Audio backend dependencies (see `README.md` for the full list and the
current Pyo API conceptual map):

```
brew install flac ffmpeg liblo libsndfile portaudio portmidi
```

When running Python from the CLI, use `uv run` (for example, `uv run python
script.py` or `uv run python -c "..."`) rather than invoking `python` directly.

To run linting instead of: `source .venv/bin/activate && ruff check src` just use `uv run ruff check src`

Patches live in `src/pyoscillate/patches/`; each is a `Patch` subclass whose
`Param`s (volume included) are the only handles to its settings and whose
`build(context: BuildContext) -> Patch` makes the graph. Patches are wired into
a project rack (a `Rack` subclass, see
[src/pyoscillate/projects/base.py](src/pyoscillate/projects/base.py)) as typed
`Slot` class attributes, grouped by `GroupController` /
`EvolvingGroup` (groups nest, and own declarative `GroupControl`s naming
`Slot`s and `Param`s), and
played through the Flet apps in `src/flet/`. Nothing is looked up by string
name. The actual implementation and runtime discipline live in the
project patch docs and the real modules under that folder.

## Implementation authority

Implementation authority is distributed, not centralized in this file: the shared patch lifecycle/runtime contract lives in [src/pyoscillate/patches/AGENTS.md](src/pyoscillate/patches/AGENTS.md), the concrete sonic concept for any given patch type lives in that patch-type directory's own instruction file (e.g. `src/pyoscillate/patches/<type>/AGENTS.md`), and the new-project workflow (README ordering, layout, patch reuse, rack wiring) lives in [src/pyoscillate/projects/AGENTS.md](src/pyoscillate/projects/AGENTS.md). Consult the nearest nested instruction set for a patch family rather than a fixed list of files here — specific modules move and get renamed as the patch set grows, so this file intentionally does not cite them.

The skill files should route into that implementation layer and explain the musical reasoning, not duplicate its implementation contracts.
