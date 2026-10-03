# Patch lifecycle: parameters, `build()`, and resource ownership

Source: a design conversation on 2026-09-26 while migrating
[drums/kick/kick.py](../../src/pyoscillate/patches/drums/kick/kick.py) from the
old module-level `PARAMETERS` + function-`build` shape to the class-based
`Patch` shape, followed the same day by an audit that replaced the first
attempt (class-body `SliderSpec`s + a `controls` dict of lambdas in `finish()`)
with the `Param` design below. `Kick` is the first (and, as of this writing,
only) patch migrated — it's the reference every other patch family converges
on. Re-read the files before relying on any detail here. Every family has
since migrated, and a second pass made the design fully static (see §7).

This file records the **why**. The terse, authoritative rule set stays in
[patches/AGENTS.md](../../src/pyoscillate/patches/AGENTS.md) — don't restate
its rules here, and don't let this file drift into a second contract. Read
this when the reasoning behind a rule there isn't obvious, or when migrating
the next patch and you want the worked example.

## 1. What lives where

| Category | Example | Lives on | Set when |
|---|---|---|---|
| Parameter (range, label, default *and* control) | `@Param(...) def punch(self, value)` | the class body | import time |
| Current parameter value | `self.punch` | the instance (stored by the `Param` descriptor) | `__init__` (as a constructor value) / plain assignment / `param.write(patch, v)` |
| Style constant | `sweep_depth = 80.0` | the leaf class body | import time |
| Live DSP graph | `self.pitch_env`, `self.body`, ..., `self.voice`, `self.sequencer` | the instance | `build()`, recreated every rebuild |

The first two rows *are* merged, deliberately: a `Param` is a data
descriptor, the same mechanism as `@property`. `Kick.punch` is the `Param`
(slider contract + control); `kick.punch` is that instance's float. The
first attempt merged them by accident instead — a class-body `SliderSpec`
shadowed by a same-named instance float — which left a type checker seeing
`self.punch` as a `SliderSpec` and let a plain `self.punch = x` skip the
live control entirely.

## 2. Construction vs. `build()`: different lifecycle stages, not redundant steps

`Patch()` and `patch.build(context)` are deliberately separate calls:

- A project rack module (e.g. `pyoscillate.projects.deep_house.rack`)
  constructs every `Patch` instance at **import time** — before any audio
  engine exists. `build()` takes a `BuildContext` - the real `Tempo`, `Clock` and
  `Harmony`, always all three - which only exist once `PatchRackApp._start_engine` in
  [flet/base.py](../../src/flet/base.py) boots the server. Calling `build()`
  from `__init__` would mean you can't even list a rack's patches without
  audio already running.
- `build()` is **repeatable on the same instance** — `PatchPanel._apply()`
  calls it again whenever a `rebuild=True` parameter changes
  (`patches/AGENTS.md` design rule 3), and again every time the patch is
  switched back on. `__init__` can't play that role; it runs exactly once.
  Because the rebuild happens on the *same* instance, `Patch._reset()`
  stops a graph that's still playing (the caller can't reach it once
  `build()` replaces `self.voice`) and parks it in `self._retired` until
  the next rebuild, so its `STOP_FADE` ramp never runs on collected
  objects.
- An unbuilt `Patch` must stay cheap and inert: a whole rack's worth of
  patches (most of which the user never switches on) get constructed as
  plain Python objects. None of them should allocate real pyo native objects
  (which generally can't even exist before `Server.boot()` anyway) until
  something actually asks for them.

So: `Patch()` = cheap, engine-independent config. `.build(context)` =
materialize (or re-materialize) the live graph now that the engine and this
build's current parameter values both exist.

## 3. Instance attributes are the only source of truth for parameter state

`Patch.__init__` seeds `self.<name>` for every `Param` in `Patch.params`
from its default (with `_built` false, so no control runs), overridden by the
matching constructor keyword (`Kick(punch=1.2)`; an unknown keyword is a
`TypeError`). From then on, **nothing else
holds a second copy of a parameter's current value** — not a shadow dict in
the Flet layer, not a "pending values" argument to `build()`.

- Assigning a `Param` (`self.punch = 1.2`, or `param.write(patch, 1.2)`
  where only the `Param` object is in hand) stores the value and, once
  the patch is built, calls the control. A `Param` with no control (a
  `rebuild=True` one) just stages the value — the caller decides
  separately whether that means a rebuild. There is no `set()`/`configure()`
  by string name: the `Param` object is the only handle.
- `build()` **takes no per-parameter kwargs**. `Kick.build(self, context)`
  reads `self.sweep_time` etc. directly, and never applies a
  parameter at all — `finish()` does that (§4).

This is what let `PatchPanel` in [flet/base.py](../../src/flet/base.py) drop
its old `self.values: dict[str, float]` shadow of the sliders: a slider move
calls `param.write(patch, value)` immediately (live-updating the running
graph if there is one), and `_apply()` only has to decide whether that also
requires a rebuild, by comparing `param.read(patch)` against a snapshot
taken at the last build for `patch.rebuild_params`. The one place a string
name is still resolved is the external boundary:
[analysis/render.py](../../src/pyoscillate/analysis/render.py)'s
`_resolve_patch` matches a CLI `--set name=value` against `param.name` by
iterating `patch.params`, then writes the `Param`.

## 4. Range is static; the control mapping is a method

`punch`'s effect is literally `self.sweep_depth * value`, and `sweep_depth`
only exists on the leaf style classes. Two different things are tangled in
that sentence, and they get opposite answers:

- The **range/default/label** can't reference `sweep_depth`, and shouldn't.
  `Kick`'s class body finishes before any style's body runs, and "Punch"
  means the same thing — 0..2× this style's own sweep depth — for every
  style. It's a style-invariant UI contract.
- The **control mapping** *can* live in the class body, because a method
  gets `self` when it's called, not when it's defined. That's the whole
  trick behind `@Param(...) def punch(self, value)`: the class body
  declares range and mapping together, and the mapping reads
  `self.sweep_depth` and `self.pitch_env` at call time, when both exist.
  No placeholders are needed for graph nodes — class-level annotations
  (`pitch_env: TrigEnv`) document them, and the descriptor only runs a
  control once `_built` is true.

The first attempt missed the second point and kept the mapping in `build()`,
which meant writing four of the five mappings twice: once as the
constructor's initial value (`mul=self.sweep_depth * self.punch`) and again
in the `controls` lambda. Now `build()` constructs nodes with neutral values
and `finish()` → `_bind()` runs every control once with the current value,
so each mapping is written exactly once.

When one style genuinely needs a different default or range, it redeclares
just that parameter — `punch = Kick.punch.replace(default=1.4)` — keeping
the control. `__init_subclass__` merges it into the inherited `params`
in place, preserving slider order. `volume` works the same way:
`volume = Patch.volume.replace(default=1.5)`.

**Both are available:** a control method can set anything, while
`self.live(Cls.param, time=...)` returns a retained `SigTo` that follows the
`Param` automatically (assigning the parameter glides it), so a node that can
take a signal needs no control at all. Targets that can't take a signal (a
clock division's steps, `Adsr` attack) keep a control method.

## 5. Retention: graph nodes on `self`

The resource-ownership rule exists because pyo's arithmetic results don't
hold their operands. Checked 2026-09-26: after `prod = a * n; mix = prod +
a; d = Disto(mix)` and dropping the names, `a`, `n`, and `prod` were
collected; only `mix` (held by `Disto` as its input) survived. A collected
node the audio thread still reads can segfault the process in a way Python
can't catch.

So retention is still mandatory; what changed is how it's expressed.
`build()` stores every node as a `self.` attribute (declared on the class),
and `_bind()` appends every public pyo object on the instance to
`self.resources`, skipping `self.voice` and anything already retained. That
retains every named node without a hand-maintained `resources=(...)` tuple
and without monkeypatching pyo constructors (the rejected alternative).
`retain()` stays for objects that never become attributes — the table
inside `envelope()`, lists like bell's `self.triggers` — and `finish()`'s
`resources=` kwarg covers anything else a patch must keep alive.

Splitting `build()` into several helper methods is still the right call
when styles need genuinely different *behaviour* — see `FmBass.tone()` in
[tonal/bass/fm/fm.py](../../src/pyoscillate/patches/tonal/bass/fm/fm.py) —
and storing nodes on `self` makes that easier, since there's nothing to
thread across method boundaries.

## 6. The rack is typed, too

A rack (`projects/base.py`) is pure class attributes - no `build_groups()`.
Each patch is a `Slot(PatchClass, param=value, ...)`, slots are grouped by
`GroupController(title, slots)`, and
`Rack.__init__` binds fresh patches and groups per rack. Each declaration is a
descriptor: on the class it is the immutable declaration (what a
`SidechainSource(kick_group, ...)` or `SlotTarget(slot, ...)` points at), on
an instance it is that rack's runtime (`rack.pad_wash` is the bound
`SoundscapeWash`). Groups nest and own their sliders: a
`GroupControl(SliderSpec(...), targets)` is declarative too. A `SlotTarget`
names a `Slot` and each `ParamControl` a `Param` object, so applying it assigns
`Param`s directly on that rack's patches - where two alternatives differ each
has its own target, so there is no "which style is active" branch and no `None`
check. A `FanOut` does the same for every patch in the group that has the
`Param`, and a target that is an inner group's `GroupControl` passes the
amount down, so an outer slider moves the inner ones. `PatchRack`, `MacroSpec`, notebooks and
the committed `presets/` folders no longer exist; `PatchRackApp` takes the
`Rack` and a `catalog_dir` for preset JSON created on demand.

## 7. Adding or migrating a patch

1. Declare each parameter as `@Param(min, max, step, default, label, help)`
   on a method named after it, whose body is the live control. A parameter
   with no control becomes `name = Param(...)`, with `rebuild=True` if it
   changes topology. Use `rate_param(base_division, help)` for the clocked
   rate.
2. Declare the graph nodes as class annotations, and in `build(self,
   context: BuildContext)` assign every node to `self.<name>`. Construct them
   with neutral values; don't repeat a parameter's mapping in the
   constructor.
3. End with `return self.finish(self.voice_node)`.
4. Callers need no change: `PatchPanel`, `analysis.render`, and
   [tests/test_deep_house_patches.py](../../tests/test_deep_house_patches.py)
   build with a `BuildContext` and assign `Param`s directly.

## Open follow-up

- `_retired` keeps only one previous graph. Two rebuilds inside
  `STOP_FADE` (0.2 s) would drop the first one mid-fade; no caller does
  that today.

## Log

- 2026-09-26: design conversation with Kyle; `Kick`/`KickRound`/`KickPunch`/`KickSoft`
  migrated as the reference implementation; this doc written.
- 2026-09-26: audit. Replaced class-body `SliderSpec` + `controls` lambdas
  with the `Param` descriptor (range, value, and control in one
  declaration, each mapping applied once by `_bind()`); graph nodes moved
  onto `self` with automatic retention; `Param.replace` + merged
  `params` for per-style overrides; `_reset()` now stops and
  parks a still-playing graph on rebuild.
- Static refactor: `Param` handles replace string lookups (`set`/`configure`/
  `controls` removed); `volume` is a `Param`; `BuildContext` replaces
  `needs_tempo/needs_clock/needs_harmony`; `rebuild=True` replaces
  `rebuild_parameters`; `self.live(Param)` replaces `live("name")`; racks use
  typed attributes, `GroupControl`s and `GroupController`; evolution is per patch (`Slot(..., evolve=Evolve(bars, choices))`); `PatchRack`,
  notebooks and preset files removed.
