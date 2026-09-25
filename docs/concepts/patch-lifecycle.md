# Patch lifecycle: parameters, `build()`, and resource ownership

Source: a design conversation on 2026-09-26 while migrating
[drums/kick/kick.py](../../src/pyoscillate/patches/drums/kick/kick.py) from the
old module-level `PARAMETERS` + function-`build` shape to the class-based
`Patch` shape. `Kick` is the first (and, as of this writing, only) patch
migrated to what follows — it's meant to be the reference every other patch
family converges on. Line numbers below are from 2026-09-26; re-read the
files before relying on them.

This file records the **why**. The terse, authoritative rule set stays in
[patches/CLAUDE.md](../../src/pyoscillate/patches/CLAUDE.md) — don't restate
its rules here, and don't let this file drift into a second contract. Read
this when the reasoning behind a rule there isn't obvious, or when migrating
the next patch and you want the worked example.

## 1. Three kinds of data, three lifetimes

A `Patch` subclass mixes three categories of state that look similar (they're
all "attributes on the class or instance") but must never be merged, because
each has a different lifetime:

| Category | Example | Lives on | Set when | Shared across |
|---|---|---|---|---|
| Control contract | `punch = SliderSpec(...)` | the class body | import time | every style subclass |
| Style constant | `sweep_depth = 80.0` | the leaf class body | import time | one style only |
| Current parameter value | `self.punch` | the instance | `__init__`/`configure()`/`set()` | nothing — one instance's own state |
| Live DSP graph | `self.voice`, `self.sequencer`, `self.resources` | the instance | `build()` | nothing — recreated every rebuild |

The rest of this doc is mostly about why those rows can't collapse into
each other.

## 2. Construction vs. `build()`: different lifecycle stages, not redundant steps

`Patch()` and `patch.build(tempo, clock)` are deliberately separate calls:

- A project rack module (e.g. `pyoscillate.projects.deep_house.rack`)
  constructs every `Patch` instance at **import time** — before any audio
  engine exists. `build()` needs a real `Tempo`/`Clock` (and sometimes
  `Harmony`), which only exist once `PatchRackApp._start_engine` in
  [flet/base.py](../../src/flet/base.py) boots the server. Calling `build()`
  from `__init__` would mean you can't even list a rack's patches without
  audio already running.
- `build()` is **repeatable on the same instance** — `PatchPanel._apply()`
  calls it again whenever a `rebuild_parameters` value changes
  (`patches/CLAUDE.md` design rule 3). `GatedVoice._reset()` exists precisely
  because one instance's graph gets thrown away and remade. `__init__` can't
  play that role; it runs exactly once.
- An unbuilt `Patch` must stay cheap and inert: a whole rack's worth of
  patches (most of which the user never switches on) get constructed as
  plain Python objects. None of them should allocate real pyo native objects
  (which generally can't even exist before `Server.boot()` anyway) until
  something actually asks for them.

So: `Patch()` = cheap, engine-independent config. `.build(tempo, clock)` =
materialize (or re-materialize) the live graph now that the engine and this
build's current parameter values both exist.

## 3. Instance attributes are the only source of truth for parameter state

`Patch.__init__` ([base.py:155](../../src/pyoscillate/patches/base.py))
seeds `self.<name>` for every `SliderSpec` in `parameters` from its default,
then applies any constructor overrides through `configure()`. From then on,
**nothing else holds a second copy of a parameter's current value** — not a
shadow dict in the Flet layer, not a "pending values" argument to `build()`.

- `Patch.set(name, value)` ([base.py:262](../../src/pyoscillate/patches/base.py))
  always does `setattr(self, name, value)` first, then calls
  `self.controls.get(name)` if `finish()` registered a live setter for it.
  Setting a `rebuild_parameters` name (which has no live setter) just stages
  the new value on the attribute — the caller decides separately whether
  that means a rebuild.
- `Patch.configure(**values)` ([base.py:243](../../src/pyoscillate/patches/base.py))
  is `set()` looped over a dict, silently skipping any name that isn't one
  of this instance's parameters. Used by `__init__` and by preset loading,
  where the caller is handing over a superset of names.
- `build()` **takes no per-parameter kwargs**. `Kick.build(self, tempo,
  clock)` ([kick.py:99](../../src/pyoscillate/patches/drums/kick/kick.py))
  reads `self.level`, `self.punch`, etc. directly — there is nothing left to
  apply, because whatever called `build()` already applied every override
  via `configure()`/`set()` beforehand.

This is what let `PatchPanel` in [flet/base.py](../../src/flet/base.py) drop
its old `self.values: dict[str, float]` shadow of the sliders: a slider move
calls `patch.set(spec.name, value)` immediately (live-updating the running
graph if there is one), and `_apply()` only has to decide whether that also
requires a rebuild, by comparing `getattr(patch, key)` against a snapshot
taken at the last build for the (usually empty) `rebuild_parameters` names.
The same pattern applies in
[analysis/render.py](../../src/pyoscillate/analysis/render.py)'s
`_resolve_build`: a `--set name=value` override is applied via
`voice.configure(**remaining)` before `build` is handed back, not passed
into `build` itself.

## 4. Why a `SliderSpec`'s range/default can't reference a per-style class attribute

`punch = SliderSpec(0.0, 2.0, ..., 1.0, ...)` on `Kick` and
`sweep_depth = 80.0` on `KickRound` look like they should be able to talk to
each other (`punch`'s effect is literally `self.sweep_depth * value`), but
they can't be defined in terms of one another, for a plain ordering reason:
`Kick`'s class body runs and finishes — including the `punch = SliderSpec(...)`
assignment — before `KickRound`'s class body ever runs. There is no `self`
during class-body execution, and `sweep_depth` isn't assigned a value on
`Kick` at all (it's a bare `ClassVar[float]` annotation); it only becomes
real data on the leaf subclasses, which don't exist yet.

This isn't a limitation to work around — it reflects a real, correct
separation:

- `punch`'s `SliderSpec` (range, step, default, label, help text) is the
  **style-invariant control contract**. "Punch" means the same thing —
  0..2× this style's own natural sweep depth — for `KickRound`,
  `KickPunch`, and `KickSoft` alike, per `patches/CLAUDE.md`'s "the graph
  itself is identical across styles."
- `sweep_depth` is a **per-style DSP scaling constant**, only meaningful
  combined with a live instance's `self.punch` inside `build()`'s closure —
  `lambda value: setattr(pitch, "mul", self.sweep_depth * value)`. It's read
  dynamically off `type(self)` at call time, which is exactly how a
  Template Method pattern is supposed to work: `Kick.build()` is the shared
  template, and each leaf's class attributes are the varying hook data it
  reads via `self`.

Baking `sweep_depth` into the `SliderSpec` itself would mean three separate
`SliderSpec` objects (one per style) just to vary one internal coefficient —
duplicating a genuinely shared UI contract to avoid a lookup that's supposed
to happen later anyway.

## 5. `retain()` vs. `finish()`

Both exist because they answer different questions about a different set of
objects, per `patches/CLAUDE.md` rule 4's "every object lands in exactly one
of `Patch.voice` / `Patch.sequencer` / `Patch.resources`":

- **`retain(*objects)`** is generic, incremental keep-alive bookkeeping —
  "don't let the GC collect this." It's called as objects are made, not
  saved up for the end: `GatedVoice.envelope()`
  ([common.py:99](../../src/pyoscillate/patches/common.py)) already retains
  its own table/`TrigEnv` pair the moment it builds one, before the rest of
  `build()` has even run.
- **`finish(voice, controls, resources=())`**
  ([common.py:149](../../src/pyoscillate/patches/common.py)) is the
  one-time terminal step: it designates the two structurally special
  objects (`self.voice`, driven by `start()`/`stop()`; `self.sequencer`,
  driven by `PatchRack`), merges in whatever `controls` `schedule()` already
  registered (the `rate` setter), and raises if `build()` never called
  `schedule()`. The optional `resources=` kwarg folds in a `retain()` call
  for whatever else `build()` constructed itself, so a build with no
  genuine per-style variation ends in one flat statement —
  `return self.finish(voice, {...}, resources=(body, body_signal, noise, click_signal, source))`
  — instead of a separate `self.retain(...)` line before it.

This was weighed against making retention fully automatic (hooking every
pyo object constructor during `build()`), which was rejected: it would
require monkeypatching pyo's constructors, would retain throwaway objects
nobody intended as graph state, and directly contradicts
`patches/CLAUDE.md`'s stance that "closure capture and transitive ownership
... are implementation details, not lifetime guarantees" — the explicit,
named-local style exists *because* relying on implicit lifetime behaviour is
the actual crash risk (a collected pyo node mid-callback can segfault the
process in a way Python can't catch).

It was also weighed against splitting `build()` into several helper
methods (one per subgraph). That's the right call when styles need
genuinely different *behaviour* — see `FmBass.tone()` in
[tonal/bass/fm/fm.py](../../src/pyoscillate/patches/tonal/bass/fm/fm.py) — but
`Kick`'s styles only vary by constants, so there's no natural seam to split
on, and threading `pitch`/`body`/`click_env` across method boundaries would
cost more than it saves for a graph this small.

## 6. Migration checklist for the next patch

To bring another module (e.g. `drums/clap/clap.py`) up to this shape:

1. Turn each `PARAMETERS` tuple entry into a class-body `name = SliderSpec(...)`
   attribute on the `Patch` subclass. `__init_subclass__`
   ([base.py:140](../../src/pyoscillate/patches/base.py)) auto-derives
   `parameters` (and `_parameter_names`) from these — no separate
   module-level `PARAMETERS` tuple needed.
2. Drop `**values: Any` from `build()`'s signature and delete the
   `self.configure(**values)` call at its top. Read `self.<name>` directly
   everywhere the old code read a `values[...]`/local-from-kwarg.
3. Replace a trailing `self.retain(...)` + `return self.finish(voice, controls)`
   with one `return self.finish(voice, controls, resources=(...))`.
4. No caller needs to change per patch: `PatchPanel`, `analysis.render`, and
   the shared test helper `assert_patch_lifecycle` in
   [tests/test_deep_house_patches.py](../../tests/test_deep_house_patches.py)
   already apply overrides via `configure()`/`set()` before calling `build`,
   which works whether or not that particular `build()` still accepts
   `**values` — so migrated and unmigrated patches can coexist mid-migration.

## Open follow-up

- `patches/CLAUDE.md` should get a short pointer to this doc (and the
  `**values`-free `build()` shape made the documented contract, not just
  `Kick`'s) once more than one family has migrated.
- Every other family — snare, hat, tom, cymbal, percussion, low_hat, bell,
  bass, keys, drone, texture, arp/canon/generative/chord — is still on the
  pre-migration shape (`PARAMETERS` tuple + `**values` in `build()`). Migrate
  them incrementally, extending existing families rather than rewriting them
  wholesale in one pass.

## Log

- 2026-09-26: design conversation with Kyle; `Kick`/`KickRound`/`KickPunch`/`KickSoft`
  migrated as the reference implementation (`Patch.set`/`configure` write-through,
  `build()` with no per-parameter kwargs, `GatedVoice.finish(resources=...)`);
  this doc written.
