# Patch lifecycle: parameters, `build()`, and resource ownership

Source: a design conversation on 2026-09-26 while migrating
[drums/kick/kick.py](../../src/pyoscillate/patches/drums/kick/kick.py) from the
old module-level `PARAMETERS` + function-`build` shape to the class-based
`Patch` shape, followed the same day by an audit that replaced the first
attempt (class-body `SliderSpec`s + a `controls` dict of lambdas in `finish()`)
with the `Param` design below. `Kick` is the first (and, as of this writing,
only) patch migrated — it's the reference every other patch family converges
on. Re-read the files before relying on any detail here.

This file records the **why**. The terse, authoritative rule set stays in
[patches/CLAUDE.md](../../src/pyoscillate/patches/CLAUDE.md) — don't restate
its rules here, and don't let this file drift into a second contract. Read
this when the reasoning behind a rule there isn't obvious, or when migrating
the next patch and you want the worked example.

## 1. What lives where

| Category | Example | Lives on | Set when |
|---|---|---|---|
| Parameter (range, label, default *and* control) | `@Param(...) def punch(self, value)` | the class body | import time |
| Current parameter value | `self.punch` | the instance (stored by the `Param` descriptor) | `__init__`/`configure()`/`set()`/plain assignment |
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
  (`patches/CLAUDE.md` design rule 3), and again every time the patch is
  switched back on. `__init__` can't play that role; it runs exactly once.
  Because the rebuild happens on the *same* instance, `Patch._reset()`
  stops a graph that's still playing (the caller can't reach it once
  `build()` replaces `self.voice`) and parks it in `self._retired` until
  the next rebuild, so its `STOP_FADE` ramp never runs on collected
  objects. Before this, `PatchRack.start()` stopped the *new* graph and
  the old output chain was never explicitly stopped.
- An unbuilt `Patch` must stay cheap and inert: a whole rack's worth of
  patches (most of which the user never switches on) get constructed as
  plain Python objects. None of them should allocate real pyo native objects
  (which generally can't even exist before `Server.boot()` anyway) until
  something actually asks for them.

So: `Patch()` = cheap, engine-independent config. `.build(tempo, clock)` =
materialize (or re-materialize) the live graph now that the engine and this
build's current parameter values both exist.

## 3. Instance attributes are the only source of truth for parameter state

`Patch.__init__` seeds `self.<name>` for every entry in `parameters` from
its default (with `_built` false, so no control runs), then applies any
constructor overrides through `configure()`. From then on, **nothing else
holds a second copy of a parameter's current value** — not a shadow dict in
the Flet layer, not a "pending values" argument to `build()`.

- Assigning a `Param` (`self.punch = 1.2`, or `Patch.set("punch", 1.2)`,
  which does the same after validating the name) stores the value and, once
  the patch is built, calls the control. A `Param` with no control (a
  `rebuild_parameters` name) just stages the value — the caller decides
  separately whether that means a rebuild. `Patch.set` also still consults
  `self.controls` for unmigrated patches.
- `Patch.configure(**values)` is `set()` looped over a dict, silently
  skipping any name that isn't one of this instance's parameters. Used by
  `__init__` and by preset loading, where the caller is handing over a
  superset of names.
- `build()` **takes no per-parameter kwargs**. `Kick.build(self, tempo,
  clock)` reads `self.sweep_time` etc. directly, and never applies a
  parameter at all — `finish()` does that (§4).

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
the control. `__init_subclass__` merges it into the inherited `parameters`
in place, preserving slider order.

**Considered and not chosen:** backing every parameter with a live `SigTo`
and writing the graph in signal arithmetic (what `ContinuousVoice.live()`
does). It needs no control methods at all and smooths zipper noise, but
some targets can't take a signal (a clock division's steps, `Adsr` attack,
funk bass's per-note state dict), so it still needs a fallback. A control
method covers both — it can set `self.some_sig.value` where smoothing
matters.

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
`resources=` kwarg stays for unmigrated patches that still use locals.

Splitting `build()` into several helper methods is still the right call
when styles need genuinely different *behaviour* — see `FmBass.tone()` in
[tonal/bass/fm/fm.py](../../src/pyoscillate/patches/tonal/bass/fm/fm.py) —
and storing nodes on `self` makes that easier, since there's nothing to
thread across method boundaries.

## 6. Migration checklist for the next patch

To bring another module (e.g. `drums/clap/clap.py`) up to this shape:

1. Turn each `PARAMETERS` entry into a `@Param(min, max, step, default,
   label, help)` decorating a method named after the parameter, whose body
   is the old `controls` lambda (`self.node.attr = f(value)`). A parameter
   with no live control becomes a bare `name = Param(...)`. Use
   `rate_param(base_division, help)` for the clocked rate.
2. Declare the graph nodes as class annotations, and in `build()` assign
   every node to `self.<name>` instead of a local. Construct them with
   neutral values; don't repeat a parameter's mapping in the constructor.
3. Drop `**values: Any` from `build()` and its `self.configure(**values)`.
4. End with `return self.finish(self.voice_node)` — no `controls` dict, no
   `resources=` tuple.
5. No caller changes: `PatchPanel`, `analysis.render`, and
   `assert_patch_lifecycle` in
   [tests/test_deep_house_patches.py](../../tests/test_deep_house_patches.py)
   apply overrides via `configure()`/`set()` before calling `build`, so
   migrated and unmigrated patches coexist.

## Open follow-up

- Every other family — snare, hat, tom, cymbal, percussion, low_hat, bell,
  bass, keys, drone, texture, arp/canon/generative/chord — is still on the
  pre-migration shape (`PARAMETERS` tuple + `controls` dict + `**values` in
  `build()`). Migrate them incrementally, extending existing families
  rather than rewriting them wholesale.
- `ContinuousVoice.live()` registers into `self.controls`; once a
  continuous patch migrates, its `@Param` controls can set a `SigTo`'s
  `value` directly and `live()` can go.
- `_retired` keeps only one previous graph. Two rebuilds inside
  `STOP_FADE` (0.2 s) would drop the first one mid-fade; no caller does
  that today.

## Log

- 2026-09-26: design conversation with Kyle; `Kick`/`KickRound`/`KickPunch`/`KickSoft`
  migrated as the reference implementation (`Patch.set`/`configure` write-through,
  `build()` with no per-parameter kwargs, `GatedVoice.finish(resources=...)`);
  this doc written.
- 2026-09-26: audit. Replaced class-body `SliderSpec` + `controls` lambdas
  with the `Param` descriptor (range, value, and control in one
  declaration, each mapping applied once by `_bind()`); graph nodes moved
  onto `self` with automatic retention; `Param.replace` + merged
  `parameters` for per-style overrides; `SliderSpec.pyo_refs` /
  `PyoParamRef` removed (unused at runtime); `_reset()` now stops and
  parks a still-playing graph on rebuild.
