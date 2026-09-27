# Project routing and operating notes

This repository uses a small set of explicit entry points instead of collapsing all project knowledge into one file.

## Entry points

- [AGENTS.md](AGENTS.md) — project-level operating instructions, implementation authority, and the project scaffolding workflow
- [.claude/skills/music-theory/SKILL.md](.claude/skills/music-theory/SKILL.md) — composition, harmony, form, rhythm, and genre reasoning
- [.claude/skills/pyo-music/SKILL.md](.claude/skills/pyo-music/SKILL.md) — sonic/perceptual translation between musical intent and DSP mechanism

## Route selection

- For pure music-theory and composition questions, load [.claude/skills/music-theory/SKILL.md](.claude/skills/music-theory/SKILL.md).
- For sound-design or synthesis translation, load [.claude/skills/pyo-music/SKILL.md](.claude/skills/pyo-music/SKILL.md).
- For patch architecture, rack wiring, project scaffolding, runtime guidance, or new-project creation, use [AGENTS.md](AGENTS.md).

## New project creation

When the user requests a new project such as a new named app or rack, this is a project-level concern and should be handled in [AGENTS.md](AGENTS.md), not inside the synth-only music bridge. The workflow there should cover:

- app package creation under `src/flet/{project_name}/`
- rack definition under `src/pyoscillate/projects/{project_name}/`
- patch-family reuse before new-module creation
- Flet app preset structure
- README and musical brief documentation

The music skill should still inform the sonic and musical brief, but the actual project scaffolding workflow belongs in the project-level file.

## Implementation authority

Concrete implementation guidance is distributed rather than listed here: the shared patch lifecycle/runtime contract lives in [AGENTS.md](AGENTS.md) and [src/pyoscillate/patches/AGENTS.md](src/pyoscillate/patches/AGENTS.md), and the sonic concept for any given patch type lives in that patch-type directory's own instruction file. Consult the nearest nested instruction set rather than a fixed file list \u2014 specific modules move and get renamed as the patch set grows.

These are the real sources of truth for patch architecture and runtime behavior.
