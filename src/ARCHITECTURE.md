# src Architecture

This document describes the shape of `src/` — the runtime layers, how they
compose, and the contract a concrete implementation must satisfy. It does
not enumerate every patch family or every project; those are covered by the
nested `AGENTS.md` files cited throughout, and by the sonic-reasoning skills
outside `src/`. This file is about *structure*, not sound design.

Code authored under `src/pyoscillate/` follows
[`pyoscillate/AGENTS.md`](pyoscillate/AGENTS.md): keep values and behavior in
the class that owns them rather than adding module-level constants, state, or
helper functions.

`src/` has two top-level packages with distinct jobs:

- `pyoscillate/` — the DSP/runtime library: patches, shared timing/harmony
  state, and audio analysis. No UI code.
- `flet/` — the UI layer: one Flet app per project, thin wiring over the
  library above. No DSP code.

## `pyoscillate/`: runtime library

### Shared rack-level state

Every patch in a rack agrees on the same clock and, for pitched material,
the same key/chord. These live once per rack, passed into patches, never
duplicated inside them:

- `tempo.py` (`Tempo`) — BPM converted to note durations in seconds.
- `clock.py` (`Clock`, `NoteDivision`) — the shared tick source a patch
  schedules against; `NoteDivision` is the fixed vocabulary of musical
  subdivisions a rate control can move through.
- `harmony.py` (`Harmony`) — rack-level key and chord progression, looked up
  by bar index so every pitched patch changes chord together.
- `analysis/` — offline/runtime audio analysis (feature extraction,
  rendering) that consumes the library to inspect/validate output; not part
  of the patch runtime itself.

### `patches/`: the patch family layer

Full contract: [patches/AGENTS.md](pyoscillate/patches/AGENTS.md). In outline:

- **Directory = patch type** — one sonic/musical role per directory (kick,
  bass, drone, ...), never one per project. Each directory: its own
  `AGENTS.md` (sonic concept) + implementation module(s).
- **Two runtime bases** (`patches/base.py`, `patches/common.py`):
  - `GatedVoice` — event-articulated (trigger/gate opens an envelope per
    hit/note): drums, tonal notes, transitions, samples.
  - `ContinuousVoice` — ungated, free-running, driven by modulation (LFOs,
    chaos), no start/end per event: drones, textures.
  - Both share one `Patch` lifecycle (construct → configure → build →
    start/stop → rebuild) and both return a `Patch` from `build()`.
- **One family class per directory, one small subclass per style** — the
  family class owns the graph and every `@Param` control; a style subclass
  only overrides profile data or a hook method, never the graph shape.
- **`@Param`** — single declaration point for a musical control (range,
  step, default, label, help text, live-update method). Perceptual names
  (`Punch`, `Body`, `Warmth`), never raw DSP terms.
- **Retained ownership** — `build()` assigns every Pyo node to `self`;
  `finish()` retains them, because an unretained Pyo wrapper can be
  collected out from under a still-running native object and crash audio.

#### Reference implementation

[`patches/drums/kick/kick.py`](pyoscillate/patches/drums/kick/kick.py) is
the concrete example every other patch module is migrating to match. What
each required piece is *for*:

- **`@Param`** — fuses three things that would otherwise drift apart into
  one declaration: the slider spec (range/default), the current value, and
  the setter that reaches the running graph. `self.<name>` is all three at
  once.
- **`build()`** — constructs the Pyo graph, separately from constructing the
  Python object, because the graph is expensive/stateful and the object
  isn't:
  - lets a whole rack be listed/configured before any audio server exists
  - lets a graph be rebuilt in place without losing the instance or its
    values
  - only ever uses neutral/style-constant values — never bakes a param's
    current value into a constructor (that mapping is the param's control's
    job)
- **`finish()`** — closes the gap between "graph exists" and "graph is
  ready to run"; two jobs every patch needs and none should reimplement:
  - retains every node `build()` created (crash prevention)
  - runs every param's control once against its current value (so a
    rebuilt graph starts in the state its sliders already claim)
  - skipping this, or hand-rolling it per patch, defeats the point of the
    shared base classes
- Together they answer three questions a slider move raises: what can this
  be set to (`@Param`), how is the sound made (`build()`), how does a
  post-build change reach it safely (`finish()` + the control method).
- Style subclasses (`KickRound`, `KickPunch`, `KickSoft`, `KickLofi`) only
  ever supply profile data or hook overrides — never touch this contract.

### How class attributes are updated, and when

- **`@Param`-declared attributes** (`level`, `punch`, `rate`, ...) — per-
  *instance* current values, declared on the class:
  - assigning `self.<name>` (directly, via `set()`, or `configure()`)
    updates the stored value immediately
  - if already built, also re-runs that param's control against the new
    value, reaching the live graph
  - before `build()`, assignment just stages the value — no graph exists yet
- **Graph-node attributes** (`self.body`, `self.envelope`, ...) — annotated
  but unset on the class, since the real Pyo objects don't exist until
  `build()`:
  - written only during `build()`/`finish()`; read everywhere else
  - never reassigned outside `build()` — a topology change means a rebuild,
    not a reassignment
- **Style `ClassVar`s** (`body_freq`, `decay`, ...) — set once on the style
  subclass, read but never written at runtime.

Net effect: params update on every post-build assignment; `ClassVar`s update
only at class-definition time; graph nodes update only across a full
`build()`/`finish()` cycle, never piecemeal.

### `params.py`

The `Param` descriptor and slider-spec plumbing that back `@Param` — shared
by every patch module, not specific to any one family.

## `projects/`: racks

`projects/<name>/rack.py` declares existing patch factories as
`GroupController` class attributes (`rack.pad`, `rack.lead`, and so on).
`Rack` binds those immutable declarations into fresh `GroupRuntime` objects
for one Flet app.
Planning-first:
`README.md` (musical brief + concept-to-patch mapping) precedes `rack.py`.
Concrete workflow: [projects/AGENTS.md](pyoscillate/projects/AGENTS.md).

A rack file owns *composition* only (which patch recipes, grouped how,
sharing which `Tempo`/`Clock`/`Harmony`) — no DSP, no UI. Runtime patches,
controllers, and mutable harmony belong to one `Rack` instance, never to the
class-level declarations. `GroupRuntime.active_patch` is the live selection.
Rack-specific constants and helper behavior belong to the rack subclass;
at module scope, a rack module contains its docstring, imports, and rack class
definition only.

## `flet/`: UI layer

`flet/base.py` (`PatchRackApp`, `PatchPanel`, `PatchGroup`) is the one
generic adapter between a `Patch` instance and a Flet UI:

- renders an enable switch, `@Param` sliders, a volume slider
- handles preset save/load and server start/stop
- every `flet/<project>/` app is a thin composition over that adapter — no
  patch internals imported, no hand-built sliders; a missing control is
  fixed in `@Param` declarations or `base.py`, never in the project app

## How the layers compose

```
tempo.py / clock.py / harmony.py   (shared rack-level state)
              │
              ▼
patches/<family>/<module>.py       (GatedVoice or ContinuousVoice subclass,
                                     @Param controls, build() graph)
              │  instances composed into GroupControllers
              ▼
projects/<name>/rack.py            (one rack per project)
              │  GroupControllers passed in
              ▼
flet/<name>/app.py  →  flet/base.py (PatchRackApp/PatchPanel: generic UI)
```

Sound design and musical decisions belong in the music-theory and
pyo-music skills and in each patch-type directory's own `AGENTS.md`; this
file only covers how the code in `src/` is put together.
