# TODO: object-oriented `Rack` base class, replacing static rack modules

Source: a design conversation on 2026-09-27 about `src/pyoscillate/projects/lofi/rack.py`
looking out of step with the rest of the object-oriented codebase — a project
rack today is a module-level `PATCHES` dict plus a hand-synced `GROUP_TITLES`
dict plus a `PATCH_GROUPS` list comprehension, plus separate `BPM`,
`TICKS_PER_BAR`, `HARMONY`, `GROUP_CONTROLLERS` globals that each `app.py`
re-imports by name and manually repacks into an `EngineSpec`. The fix is an
abstract `Rack` base class: a project rack becomes one class with declared
class attributes and a `build_groups()` method: `PatchRackApp` takes a `Rack`
instance directly, through a known interface, instead of two loose values
assembled by each `app.py`.

## How to use this file (for future sessions)

1. Work through the tasks in order — task 1 (the `Rack` base + `PatchRackApp`
   interface change) must land before any per-project rack can migrate.
2. Before editing, re-read the files a task touches — they may have changed
   since 2026-09-27.
3. Respect the existing layering:
   - [src/pyoscillate/patches/CLAUDE.md](../../src/pyoscillate/patches/CLAUDE.md) — patch runtime contract, unaffected by this change (a `Rack` only assembles already-built `Patch` instances, it doesn't touch their lifecycle).
   - [src/flet/base.py](../../src/flet/base.py) — `PatchGroupDef`/`EngineSpec`/`PatchRackApp` stay as the shared Flet-facing types; `Rack.engine_spec()` builds an `EngineSpec` from the rack's own attributes rather than `EngineSpec` being assembled ad hoc in each `app.py`.
   - [CLAUDE.md](../../CLAUDE.md) new-project workflow step 6 ("Wire the rack") — update this once the shape lands, so future projects are told to subclass `Rack` from the start rather than writing module constants.
4. Keep the design decision from the conversation: `needs_clock` (and every other `EngineSpec` field) is an explicit class attribute a project sets on its `Rack` subclass — none of it is derived by scanning `build_groups()`'s patches for `needs_clock`/`needs_tempo` flags.
5. When a task is done, tick it here, note the commit or files, and add anything learned to the Log.
6. Use `uv run` for any Python (for example `uv run pytest`, `uv run ruff check src`).

## Design (agreed 2026-09-27)

- **`Rack`** (new, `src/pyoscillate/projects/base.py`), an `ABC`:
  - Class attributes with sensible defaults, each overridden by a subclass as needed: `bpm: float | None = None`, `ticks_per_bar: int = DEFAULT_TICKS_PER_BAR`, `needs_clock: bool = False`, `harmony: Harmony | None = None`, `group_controllers: tuple[GroupController, ...] = ()`, `nchnls: int = 2`, `master_output_default`/`master_output_max` (defaulting to `flet/base.py`'s existing `MASTER_OUTPUT_DEFAULT`/`MASTER_OUTPUT_MAX`).
  - `build_groups(self) -> tuple[PatchGroupDef, ...]` — abstract. A project rack constructs every patch instance and its `PatchGroupDef` grouping here, replacing today's `PATCHES`/`GROUP_TITLES`/`PATCH_GROUPS` trio.
  - `groups` — a `functools.cached_property` calling `build_groups()` once, so patch instances are constructed exactly once per `Rack()` instantiation (same timing as today's module-import-time construction).
  - `engine_spec(self) -> EngineSpec` — concrete, not overridden per project; builds an `EngineSpec` straight from the class attributes above.
- **`PatchRackApp.__init__`** (`src/flet/base.py`) changes from `(page, title, subtitle, patch_groups: list[PatchGroupDef], engine: EngineSpec, catalog_dir=None)` to `(page, title, subtitle, rack: Rack, catalog_dir=None)`. Internally: `patch_groups = list(rack.groups)`, `engine = rack.engine_spec()`. Nothing downstream of those two values changes.
- **Each project's `rack.py`** becomes a single `class <Project>Rack(Rack):` with the tempo/harmony/controller class attributes (each keeping its existing explanatory comment) and a `build_groups()` returning the same `PatchGroupDef` tuple the old `PATCH_GROUPS` list comprehension produced.
- **Each project's `app.py`** shrinks to importing `<Project>Rack` and calling `PatchRackApp(page, title, subtitle, <Project>Rack(), catalog_dir=...)` — no more re-importing `BPM`/`HARMONY`/`TICKS_PER_BAR`/`PATCH_GROUPS`/`GROUP_CONTROLLERS` and no more constructing `EngineSpec` by hand.

## Tasks

### 1. `Rack` base class + `PatchRackApp` interface change

**Do:**
- Add `src/pyoscillate/projects/base.py` with `Rack(ABC)` as designed above.
- Change `PatchRackApp.__init__` (`src/flet/base.py`, currently ~line 376) to take `rack: Rack` in place of `patch_groups`/`engine`, deriving both from `rack.groups`/`rack.engine_spec()` at the top of the method.
- Do not change `PatchGroupDef` or `EngineSpec` themselves — `Rack.engine_spec()` is the new thing assembling an `EngineSpec`, not a replacement for the dataclass.

**Done when:** `Rack` and the new `PatchRackApp` signature exist, nothing else has been migrated yet, and every existing `app.py` is (temporarily) broken by the signature change — that's expected until task 2 lands for each project.

### 2. Migrate each project rack + app (one PR per project, or all together) — DONE

Five existing racks/apps to migrate, checked from the tree on 2026-09-27:

- `pyoscillate/projects/lofi/rack.py` + `flet/lofi/app.py` — has `GROUP_CONTROLLERS`; the reference case for every `Rack` field.
- `pyoscillate/projects/deep_house/rack.py` + `flet/deep_house/app.py` — no group controllers; confirm whether it needs `needs_clock = True` (it does today via a manually-constructed `EngineSpec`).
- `pyoscillate/projects/soundscape_fm/rack.py` + `flet/soundscape_fm/app.py`
- `pyoscillate/projects/rack_demo/rack.py` + `flet/rack_demo/app.py`
- `pyoscillate/projects/psyambient/rack.py` + `flet/psyambient/app.py`

Also check `src/flet/patch/app.py` (referenced in `patches/CLAUDE.md`'s run-comment convention, e.g. `uv run flet run src/flet/patch/app.py -- <module> style=<x>`) — confirm whether it goes through `PatchRackApp` at all, or is a single-patch dev harness outside this refactor's scope; if the latter, note that explicitly rather than migrating it.

**Do, per project:**
- Read the current `rack.py` fully before rewriting — carry over every explanatory comment on the old module constants onto the corresponding new class attribute or `build_groups()` entry; don't lose the "why" (e.g. lofi's ticks-per-bar/harmony/progression-rotation comments).
- Rewrite `rack.py` as `class <Project>Rack(Rack): ...` per the design above.
- Rewrite `app.py` to construct `<Project>Rack()` and pass it straight to `PatchRackApp`.
- Run `uv run ruff check src` and confirm the app still boots (`uv run flet run src/flet/<project>/app.py`) if you can exercise audio locally; if not, say so explicitly rather than claiming it was verified.

**Done when:** all five (or four, pending the `patch/app.py` scoping question) apps boot with the new `Rack`-based construction and no project module still defines `PATCHES`/`PATCH_GROUPS`/`BPM`/`TICKS_PER_BAR`/`HARMONY`/`GROUP_CONTROLLERS` as bare module globals.

### 3. Documentation — DONE

- [src/pyoscillate/projects/CLAUDE.md](../../src/pyoscillate/projects/CLAUDE.md) step 6 ("Wire the rack"): describe subclassing `Rack` and implementing `build_groups()` (plus the relevant class attributes) instead of writing `PATCH_DEFS`/module constants. Update the `GROUP_CONTROLLERS` mention there to `Rack.group_controllers`.
- [src/pyoscillate/patches/CLAUDE.md](../../src/pyoscillate/patches/CLAUDE.md) — likely no change needed (patch contract is unaffected), but skim it once task 1 lands in case anything there implicitly assumed the old rack-module shape.
- Root [CLAUDE.md](../../CLAUDE.md) — check whether "Patches live in..." paragraph needs a one-line update to mention `Rack`.

### 4. Tests

- Following the style in `tests/test_deep_house_patches.py` (check it still exists/matches this name before relying on it):
  - a minimal fake `Rack` subclass's `build_groups()` is called exactly once across repeated `.groups` access (`cached_property` behaviour).
  - `Rack.engine_spec()` round-trips every class attribute into the matching `EngineSpec` field.
  - `PatchRackApp` constructed with a fake `Rack` produces the same `patch_groups`/engine wiring as constructing it with the old explicit `patch_groups`/`engine` args did (regression check against current behaviour, run before task 2's migration deletes the old call sites, or reconstructed from git history if that's already gone).

## Open questions

- Should `needs_clock` eventually be derivable (`any(p.needs_clock or p.needs_tempo for g in groups for p in g.patches)`) with the explicit attribute as an override-only escape hatch, instead of always explicit? Decided 2026-09-27: keep it explicit only, for now — revisit if keeping it in sync with patch flags becomes a recurring source of bugs.
- Scope of `src/flet/patch/app.py` — resolve during task 2's per-project pass rather than guessing here.
- Whether `Rack` subclasses should be singletons/constructed once at app-module level vs. per `main()` call — current design constructs one per `main()` call (matches today's per-process module-import-time construction of `PATCH_GROUPS`); revisit only if a real need for sharing a `Rack` instance across pages appears.

## Deliberately out of scope

- Any change to `Patch`, `PatchGroupDef`, `EngineSpec`, `GroupController`, or the patch runtime contract — this refactor only replaces how a project assembles and hands over its groups/engine config, not the shapes themselves.
- Turning `PatchGroupDef` construction inside `build_groups()` into something more declarative (e.g. class-level field declarations) — a plain method returning a tuple is enough; don't add a second builder DSL on top of it unless a real pain point shows up.

## Log

- 2026-09-27: design discussed and agreed across two rounds (initial `engine_spec()`-called-by-`app.py` shape, then corrected so `PatchRackApp` takes the `Rack` instance directly); this plan written. No code changed yet.
- 2026-09-27: task 2 done. All five project racks (`lofi`, `deep_house`,
  `soundscape_fm`, `rack_demo`, `psyambient`) rewritten as `Rack` subclasses;
  their `app.py`s now construct `<Project>Rack()` and pass it straight to
  `PatchRackApp`. `src/flet/patch/app.py` *does* go through `PatchRackApp`
  (it wasn't a harness-outside-the-refactor case as the open question
  speculated), so it got a `SinglePatchRack(Rack)` wrapper built at runtime
  from the CLI-selected `Patch` instance, replacing its inline
  `EngineSpec`/`PatchGroupDef` construction. Updated three existing tests
  that imported the old module globals directly:
  `tests/test_deep_house_patches.py` (`BPM`/`PATCHES`/`TICKS_PER_BAR` →
  `DeepHouseRack()` attributes/`.groups`), `tests/test_flet_patch_groups.py`
  (`PATCH_GROUPS` imports → `DeepHouseRack().groups`/`PsyambientRack().groups`),
  and `tests/pyoscillate/projects/lofi/test_rack.py`'s subprocess script
  (`rack.BPM`/`rack.TICKS_PER_BAR`/`rack.HARMONY` → `LofiRack()` instance
  attributes). Full suite run after: same 14 pre-existing failures as on
  unmodified `main` (drums/clap health tests, gated-patch silence subtests,
  one flaky noise `test_depth_adds_movement` subtest) — none introduced by
  this migration; `ruff check src tests` clean.
- 2026-09-27: task 3 done. Updated `src/pyoscillate/projects/CLAUDE.md` step
  6 ("Wire the rack") to describe subclassing `Rack` and implementing
  `build_groups()` instead of writing `PATCH_DEFS`/module constants, and
  renamed the `GROUP_CONTROLLERS` mention to `Rack.group_controllers`.
  Updated root `CLAUDE.md`'s "Patches live in..." paragraph to mention the
  `Rack` subclass. Skimmed `src/pyoscillate/patches/CLAUDE.md` — no change
  needed, as expected; it never referenced the old rack-module shape.
