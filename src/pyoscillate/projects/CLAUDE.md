# New project workflow

This file is the concrete authority for creating a new project rack — the
root [CLAUDE.md](../../../CLAUDE.md) only routes here. Everything under this
directory follows it.

When the user asks for a new project named `{project_name}` (a whole new
Flet app + patch rack, not a single patch edit), use this workflow in order:

1. **Ground the request.** Start with the musical and sonic brief, then translate it through the music and pyo-music skills before creating files.
2. **Choose the project layout.** Create the project package under `src/flet/{project_name}/` and the rack under `src/pyoscillate/projects/{project_name}/` when a new app/rack is required.
3. **Write the README before implementing.** Document the musical brief and concept-to-patch mapping in `src/pyoscillate/projects/{project_name}/README.md` right after grounding, before any patch code exists — see "README before implementation" below.
4. **Reuse or extend existing patch families first.** Search the nearest patch family before creating a new module. Extend an existing family or builder when possible — per the mapping table just written.
5. **Implement the patch set.** Use the existing patch-type directories under `src/pyoscillate/patches/` and the runtime conventions described in [src/pyoscillate/patches/CLAUDE.md](../patches/CLAUDE.md) as the implementation source of truth.
6. **Wire the rack.** Put the `PATCH_DEFS` list in the project rack module and keep the app layer thin.
7. **Add presets.** Add a `presets/` folder for the Flet app when relevant.
8. **Validate the runtime contract.** Keep the patch graph and runtime state aligned with the project's patch architecture rules.

## README before implementation

Write the project's `README.md` immediately after grounding the request
(step 1: musical brief through the music-theory and pyo-music skills) and
before creating or editing any patch module or `rack.py`.

The README is the artifact of the planning conversation, not a summary
written after the fact. It must capture, at minimum:

- the musical brief (tempo/feel, harmony, form) with pointers to the
  music-theory reference files that grounded it
- a concept-to-patch mapping table: each sonic concept in the brief, the
  patch family it maps to, and whether that family is reused as-is, extended
  with a new style/parameter, or genuinely new
- the shared harmony/tempo constants the rack will use

Reasoning: the concept-to-patch mapping is exactly what forces the root
file's "don't map words directly to Pyo objects" chain to actually happen
before code exists. Writing it after implementation lets the code decide the
mapping instead of the brief, and produces a README that describes what was
built rather than one that could have been reviewed before any of it was
built.

## Consequence for implementation

Because the README is written first:

- Patch reuse-vs-extend-vs-new decisions in the mapping table are commitments,
  not options — implementation should follow the table, not re-litigate it.
  If implementation reveals the mapping was wrong, update the README's
  mapping table in the same change that changes the code.
- A project directory with a `README.md` but no `rack.py` yet is a normal,
  valid state (a planned-but-unbuilt project), not an error or leftover.
- Do not backfill a README from finished code as a substitute for this step
  on a *future* project; each new project gets its own planning-first README.
