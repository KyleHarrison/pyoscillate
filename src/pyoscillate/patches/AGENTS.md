# Patch architecture

This directory is organized by patch type — one subdirectory per sonic/musical
role (a bass family, a kick family, a drone family, and so on), never per
project. This file is the contract every patch must satisfy, and how to lay
out a new patch-type subdirectory within it. It cites one module on purpose:
`drums/kick/kick.py` is the reference implementation of the architecture
below. Beyond that, it avoids citing specific modules, which move and get
renamed. For how the shared framework itself works — the `Patch` lifecycle,
the Pyo graph, the clock, and parameter updates — see
[ARCHITECTURE.md](ARCHITECTURE.md).

## Read these first

- `.claude/skills/pyo-music/SKILL.md` — musical intent, synthesis strategy, and choice of Pyo objects
- [ARCHITECTURE.md](ARCHITECTURE.md) — how the shared `Patch`/`Param`/`Clock` framework works
- The nested `AGENTS.md` inside the patch-type directory you're working in — the concrete, concept-level authority for that sonic role (its sonic function, minimal architecture, and design alternatives)
- The other modules already living in that same directory — for their sound and signal graph, and for code structure, following `drums/kick/kick.py` and the contract below

The goal is simple: musical reasoning is handled by the skill, the sonic concept for a given patch type is handled by that directory's own instruction file, and this file only covers the shared implementation/runtime contract every patch must follow.

## Creating a new patch-type subdirectory

Before creating one, check whether an existing directory already covers the
musical role you need (see "Choosing a family" below) and extend it instead.

When a new role genuinely isn't covered:

1. Create `patches/<family>/` with an `__init__.py` and a `AGENTS.md`.
2. Write that `AGENTS.md` as the sonic concept for the family, described
   abstractly: its musical role, its minimal signal-chain shape, and the
   design alternatives worth knowing about. It does not restate this file's
   implementation contract, and it does not need to cite its own modules by
   name — module content is the working reference for style and shape.
3. If the directory holds a genuinely new role with no patches yet, mark the
   `AGENTS.md` "Status: placeholder" instead of writing module code. Fill it
   in from sources and drop the placeholder status when the first patch in
   it is implemented.
4. Add one module per implementation, following "Module anatomy" below, with
   a family base class (subclassing `common.GatedVoice` or
   `common.ContinuousVoice`, see [ARCHITECTURE.md](ARCHITECTURE.md)) and one
   small style subclass per variant.
5. List instances directly in a project rack's `GroupController` — a patch
   module never wires its own UI (design rule 6).

## Directory model

- Each patch-type directory is self-contained: its own `AGENTS.md` (sonic concept, described abstractly) plus one or more implementation modules (concrete builders/profiles for that concept).
- Before creating a new directory, check whether an existing one already covers the musical role you need and extend it instead.
- When a patch-type directory's `AGENTS.md` is still empty, treat the existing modules in that directory as the working reference for style and shape until it is filled in — do not backfill this file with citations to fill that gap.

## Layered archetype model

Organize the patch collection by function, not by implementation detail.

### Layer A: fundamental sound mechanisms

These are reusable DSP ideas that can appear in many families:

- oscillator and resonator behavior
- attack, decay, and release envelopes
- pitch envelopes and filter envelopes
- noise excitation and transient generation
- amplitude shaping and saturation
- FM, detuning, ring modulation, and waveshaping
- delay, chorus, and reverb
- slow LFO motion and chaotic drift

These answer: “What physical signal change creates this sound?”

### Layer B: sound archetypes

These are recognisable sound families, each defined by how the mechanism is combined into a musical object:

- drums: kick, snare, clap, hat, cymbal, tom, percussion, shaker
- pitched percussion: bell
- tonal voices: bass (with acid, fm, funk, reese sub-families), pluck, lead, pad, drone, keys, strings
- texture families: atmosphere, texture, rumble, noise
- sample families: playback, breakbeat, grains
- transition families: riser

These answer: “How are those mechanisms combined to create a recognisable sound family?”

Some directories are **placeholders**: they hold an `__init__.py` and a
`AGENTS.md` marked "Status: placeholder", but no patches yet. They record
roles a complete electronic toolkit needs. When you implement the first patch
in one, fill in its `AGENTS.md` from sources first, then drop the placeholder
status.

Outside the archetype layers, `utility/` (click, sine) holds reference and
test signals, not musical voices.

#### Choosing a family

Place a patch by how it is *used*, not by register or mood words. Two
questions, borrowed from modular practice, decide it:

1. **Gated or ungated?** A gated voice is articulated by events: a trigger or
   gate opens the amplitude through an envelope, so every note or hit has a
   start and an end (in code: a clocked or metro-driven trigger feeding an
   envelope). An ungated voice has its amplitude held open and runs
   continuously; its interest comes from modulation — LFOs, random, chaos,
   slow swells (in code: typically a `ContinuousSequencer`).
2. **For ungated voices, is there a stable pitch centre?**

```text
gated   → role decides: drums/, pitched_percussion/,
          tonal/bass (low-register note lines), tonal/lead, tonal/pluck,
          tonal/pad (sustained chords whose harmony changes on events),
          tonal/keys, tonal/strings, sample/ (recorded source),
          transition/ (one-shot gestures that mark form)
ungated → stable pitch centre → tonal/drone   (any register; "sub" is a register, not a family)
        → no pitch centre     → texture/      (noise, grains, chaos-as-timbre)
```

Consequences worth keeping explicit:

- "Low" does not mean `tonal/bass`. A continuous sub bed is a drone; an
  unpitched low rumble is texture. `tonal/bass` is for basslines.
- "Ambient" or "atmospheric" does not name a family. Decide gated/ungated and
  pitch centre first.
- A pad carries changing harmony; a drone holds one centre and evolves in
  timbre, level, or micro-pitch.
- **Soundscape is a rack-level concept, not a patch family.** A soundscape is
  an arrangement of layers — a keynote bed (drones, textures), foreground
  signals (events, melodies), and distinctive soundmarks — so it belongs in a
  project rack under `src/pyoscillate/projects/`, composed from these
  families.

### Layer C: musical structure

These are not synthesis archetypes. They describe how a sound is organised in musical time:

- arp
- chord
- generative
- canon
- clock_tick

These answer: “How is the sound arranged rhythmically, melodically, or structurally over time?”

The operational rule is simple: sound archetypes describe construction; musical structures describe organisation.

## Patch contract

A module defines one family class (a `Patch` subclass, usually via a
directory-level base) plus one small subclass per style. A project rack declares
it as a `Slot` in a `GroupController`. `name`/`title`/`summary` are
plain class attributes, derived in `__init_subclass__` from the class name and
docstring unless the class body assigns its own. The constructor takes only
`Param` values (`Kick(punch=1.2, volume=1.6)`; an unknown key is a `TypeError`);
sidechains are bound by the rack - there are no `name=`/
`title=`/`summary=`/`volume=` arguments, so a different title means a subclass.

### Bases

- `common.GatedVoice` (named `drums.base.DrumVoice` in the drums family) —
  event-articulated voices. Provides `self.trigger`, `self.envelope(...)`
  (an `ExpTable` + `TrigEnv` off the trigger, auto-retained),
  `self.schedule(base_division, rate, clock)` (subscribes `self.next_step`;
  `schedule_with(..., callback)` takes an explicit callback), `self.reschedule()`,
  and `self.step_pattern(cycle, pattern)`, which returns a callable giving a
  `Step(index, hit, value)`. What a voice plays is chosen from the shared
  pattern catalogs (see "Patterns" below), never declared inline.
- `common.ContinuousVoice` — ungated, free-running voices; its sequencer is
  a no-op `ContinuousSequencer`.

**Patterns.** Every step pattern lives once in `theory/intervals.py`, as a
member of `Rhythm` (hit velocities), `Melody` (semitone offsets above the
chord root, with optional accents and lengths) or `ChordTones` (chord-tone
indexes); a member is `(division, cycle, entries, label)`. A patch never
defines its own: it mixes in `Rhythmic`, `Melodic` or `Figured` (`common.py`),
which add a dropdown `Param` (`rhythm`/`melody`/`figure`) over the whole
catalog, schedule on the chosen pattern's own grid and swap it live. A style
names its starting pattern with `rhythm = Rhythmic.rhythm.replace(default=
Rhythm.X.index)` and, for `on_evolve`, rotates by assigning the `Param`
(`self.rhythm = variant.index`), so the dropdown stays the single source. A
pattern a patch needs that the catalog lacks is added there (append only: a
saved dropdown index must keep meaning the same pattern), so every other patch
can play it too. `base_division` stays on the class only to set the range of
the `rate` slider.

**`Step.hit` vs `Step.value`.** `hit` says whether the pattern has an event at
the step (structure); `value` says what the event carries (an accent, a pitch
offset, `True` for a plain set), and is meaningless when `hit` is False. Test
`hit` for rhythm and read `value` only after it. A pattern whose value is also
its level (velocity-as-structure: a value that rounds to 0 is a rest, anything
else sets loudness) should still produce both fields, so callbacks never
infer a rest from a magic value.

Both provide `finish(voice, *, resources=())`. `GatedVoice.finish` raises if `build()` never
called `schedule()`.

### Module anatomy (follow `Kick`'s order)

1. A run comment (`# uv run flet run src/flet/patch/app.py -- <module>`),
   then a module docstring describing the sound and its mechanism.
2. Class constants for plain shared data (break-point lists, curve shapes),
   owned by the family class that uses them.
3. The family class body, in this order:
   - `volume = Patch.volume.replace(default=...)` when the patch's default
     output level differs, and `base_division`.
   - Style-invariant DSP constants as `ClassVar`s with values.
   - Per-style profile data as bare `ClassVar` annotations (no value) — each
     style subclass supplies them.
   - Graph node annotations (`body: Sine`, `body_signal: PyoObject`, ...) —
     one per node `build()` assigns. These declare the graph; don't give
     them placeholder values.
   - One `@Param` per parameter (see below), then `rate = rate_param(...)`
     for clocked patches.
   - `build()`.
4. Style subclasses: a docstring, optionally `summary`, and the profile
   data — nothing else unless the style's behaviour genuinely differs.

### Parameters: `@Param`

Each parameter is declared once, as a decorated method named after it:

```python
@Param(minimum, maximum, step, default, "Label", "What you hear when you move it.")
def punch(self, value: float) -> None:
    self.pitch_env.mul = self.sweep_depth * value
```

- The method body is the **live control**: it maps the value onto the
  running graph. It may read style constants and other nodes off `self`.
- `self.punch` is the instance's current value. Assigning it (`patch.punch =
  1.2`, or `param.write(patch, 1.2)`) stores it and, once built, runs the
  control. The `Param` object is the only handle: nothing looks a parameter
  up by its string name, and nothing else may hold a copy of its value.
  `volume` is itself a `Param` on `Patch`.
- Controls run once at the end of every build and again on every change, so
  they must be cheap, idempotent attribute writes. Never construct a Pyo
  object inside a control.
- A parameter only read by a sequencer callback (e.g. a note length or
  accent depth applied per step) needs no control: declare it as
  `name = Param(...)` and read `self.name` in the callback. Don't mirror it
  into a state dict.
- A parameter that changes topology is declared `rebuild=True`; the Flet
  layer rebuilds the patch when it changes (`Patch.rebuild_params`).
- A parameter that should only glide a graph node needs no control: hand the
  node `self.live(Cls.param, time=...)`, a retained `SigTo` that follows the
  `Param` whenever it is assigned.
- A parameter a listener could want moving by itself declares `sweep=True`.
  Each patch instance then owns a `Sweep` (`patches/sweep.py`): a pyo
  triangle `LFO` that bounces the parameter between a `low` and a `high`, one
  there-and-back cycle every N bars, pushed through the parameter's own
  control. The resting value (`self.<param>`) is never overwritten. Only
  parameters with a live control (or a `live()` signal) can sweep: not
  `rebuild` parameters, and leave off `scale="note"` and `rate` ones. A rack
  starts one enabled with `Slot(..., sweeps=(ParamSweep(Cls.param, low, high,
  bars),))`; the Flet layer adds the toggle and range slider itself.
- Pitch parameters in Hz take `scale="note"` (design rule 2). A filter
  cutoff in Hz takes `scale="cutoff"`: the track runs 0-1 with a power taper
  (`step` is in track units, bounds and default stay in Hz), so the low end,
  where each step is audible, gets most of the slider. Only the per-patch slider
  applies the taper; group-control and sweep-range sliders still span the
  Hz range linearly.
- `rate_param(base_division, help)` is the clocked rate; its control calls
  `reschedule()`, so don't register a rate control by hand.

#### Macro parameters

One musical slider may drive several nodes at once (an "acid" amount that
raises filter cutoff, envelope depth and resonance together while shortening
the decay). This is a first-class pattern, not a workaround:

- The one control writes every target node. The relationships between them
  (curves, ratios, offsets) are written there, once, as style constants or
  expressions of the single value.
- Derive, never mirror: no second `Param` or state copy holding a value the
  macro can compute. If a listener also needs one target alone, give it its
  own `Param` and keep the macro for the coupled move.
- Name and describe it by what you hear change as a whole ("Acid": more bite
  and squelch), not by the nodes it touches (design rule 2).
- Controls stay cheap, idempotent attribute writes, so a macro is as live and
  as sweepable as any single-node parameter.

### `build()`

```text
self._reset()                            # always first
self.<node> = ...                        # every node, neutral values
self.schedule(...)                       # gated voices
return self.finish(self.<output node>)
```

- The signature is `build(self, context: BuildContext)` for every patch:
  `context.tempo`, `context.clock` and `context.harmony` are always fully
  populated (there are no `needs_*` flags and no `None` harmony); a patch
  ignores the parts it doesn't use. It takes no per-parameter kwargs.
- Assign every node to `self.<name>`, never a local (design rule 4).
- Construct nodes with neutral or style-constant values only. Never repeat
  a parameter's mapping (`mul=self.sweep_depth * self.punch`) in `build()`;
  `finish()` applies every control, so each mapping is written only in its
  `@Param` method.
- A sequencer callback defined inside `build()` reads nodes and parameter
  values off `self` at call time.
- `finish(voice)` sets `self.voice` and `self.sequencer`, retains every
  public Pyo object on `self`, marks the patch built, and runs every
  control with its current value. No `controls` dict.

### Style variation

- **Different profile data** (frequencies, decay times, levels): `ClassVar`
  values on the style subclass. The family's `build()` and controls read
  them via `self`.
- **Different slider default or range**: redeclare only that parameter on
  the style, keeping its control — `punch = Kick.punch.replace(default=1.4)`.
  It stays in its original slider position.
- **Different behaviour**: factor the shared steps into the family class and
  give each style a hook method to override (e.g. `FmBass.tone()`). Hook
  methods assign their nodes to `self` too.

### Lifecycle

1. **Construct** (rack import time, before any audio server exists): seeds
   each parameter from its default, then applies constructor overrides. No
   control runs and no Pyo object is created.
2. **Configure**: sliders and group controls assign `Param`s on the instance;
   values are staged on `self`.
3. **Build**: `_reset()` → graph on `self` → `finish()`. From here,
   assignment is live.
4. **Start/stop**: `start()` adds the volume/limiter/fade output chain and
   plays the sequencer; `stop()` fades out and does nothing if the patch
   isn't playing.
5. **Rebuild**: `build()` again on the same instance — when the patch is
   switched back on, or a `rebuild=True` parameter changes. `_reset()`
   stops a graph that is still playing and keeps it alive through its fade.

### Live hooks outside `@Param`

`on_evolve(self, index: int) -> None` is a no-op hook a patch may override
for rack-level, infrequent (tens-of-bars) evolution — an `EvolvingGroup`
(an `EvolvingGroup` in `controller.py`) calls it live, every N bars, on whichever patch instance is
currently active in a watched group. It is a third live-update path
alongside `@Param` controls, but deliberately not a
`@Param`: no slider, not user-facing, just a plain method
call driven by the controller's timer instead of a widget. `index` is the
controller's own fire count; an override reads it into its own musical data
(e.g. `index % len(self.SOMETHING)`) and owns its own wraparound — there's
no shared numeric range to clamp against.

### Gate add-on

A gate chops a voice's output with a clocked step pattern (for example 16
steps per bar, each open for about 70% of the step). It is an opt-in mixin,
not a family, and it never changes which family a voice belongs to: a gated
drone is still `tonal/drone`.

Gated and ungated are two ends of one mechanism. The gate's depth is how far
the output closes between pulses: at full depth a voice is silent until
triggered (a gated voice), at zero it is always open (an ungated one). A
voice's default depth is 0, so adding the gate changes nothing until a rack
or listener raises it.

Any voice may take the gate. Leave it off where it cannot work:

- a sidechain source (the kick), since the gate would shape the duck signal;
- a free-running voice (generative, canon, clock_tick) whose timing is its
  own, where a clock-locked gate would add a second, unrelated rhythm;
- a voice whose ring is the point (bell, drums), where it would only cut it.

Bass, lead, pluck, keys and chord already choose which steps play; the gate
sits on top of that as a second, independent chop.

- The mixin owns its `Param`s (`gate` depth, `gate_length`, `gate_density`,
  `gate_seed`, `gate_rate`), all live. The gate is always built; toggling it
  never rebuilds the patch. A rack enables it by constructor override
  (`Strings(gate=1.0)`), and `ParamSweep` can sweep its depth.
- `self.add_gate(source, context)` builds the `Trig`, table and `TrigEnv`,
  subscribes on the clock, and returns the gated signal. Call it in
  `build()` before `finish()`; `finish()` merges the gate's pulse with the
  voice's own sequencer in a `SequencerGroup`. A patch's `sequencer` can
  therefore be a group: read the voice's own division as `self._division`.
- Timing comes from `Pulse` (`common.py`): one clocked step source, shared
  with `GatedVoice`, whose step index comes from `(clock.tick // steps) %
  cycle`, never an internal counter, so phase survives rebuilds. A voice with
  its own pulse (per-bar chords, per-16th notes) and the gate each own one.
- Edges ramp over a few milliseconds so near-sine voices do not click. Seeded
  density keeps its pattern on the seed and step, so it repeats each cycle.
- The gate sits before the duck and volume stages, so sidechain still works
  on top and a reverb tail is chopped.
- Do not name a node `gate` or `gate_*` on a gated voice (a funk bass's note
  gate is `note_gate`); those names belong to the mixin.

### Pitch add-ons

Voices that play a note line share two live Params, so a listener can move
them without a rebuild:

- `glide` (`Bass.glide`, `Lead.glide`): seconds a note takes to slide in from
  the previous one. The voice plays from a retained `SigTo` (`self.pitch`),
  and a step sets `self.pitch.value`. The default is the voice's old sound
  (0, or 0.02 for funk and the legato lead).
- `bend` (`PitchBend` mixin, `common.py`): each struck note starts this many
  semitones off and scoops to pitch over `BEND_TIME`. `add_bend(trigger)`
  returns the frequency multiplier to multiply into the note pitch, and the
  voice must `play()` that trigger on every struck note. Default 0 is a clean
  attack.

## Design rules

### 1. Extend existing families before creating new files

Before adding a new module, look for a neighboring patch with the same musical role.

Prefer:

- extending an existing patch family
- adding a parameter to an existing family class
- adding a style subclass when the signal graph and control intent are the
  same but profile data differs, or a hook-method override when a style's
  behaviour genuinely differs

Create a new patch module only when the patch genuinely needs a new control surface, topology, or lifecycle.

### 2. Keep parameters musical, not technical

A slider should describe what the listener hears:

- `Brightness`, `Body`, `Punch`, `Warmth`, `Movement`, `Depth`, `Drive`, `Decay`, `Rate`

Avoid exposing low-level implementation names such as filter cutoff, oscillator gain, wet/dry amount, or coefficient values when a perceptual label is clearer.

The `help_text` should answer: “What will I hear if I move this slider?”

A slider that sets a pitch in Hz (Register, `root_freq`) takes
`scale="note"`: its ticks are equal-tempered semitones and its label shows
the note name, so it can only land on in-tune notes. Keep the parameter in
Hz and give its `minimum`, `maximum` and `default` as notes from
`theory/notes` (`notes.A1`, not `55`). Continuous detune belongs in its own
control, not in a Register slider with Hz steps.

### 3. Parameter changes should usually be live

If a parameter can change without changing the graph topology, give its `@Param` a control method that updates the running graph.

- `Patch.update(...)` is the standard runtime update path.
- Rebuilds are for structural choices only: new voice count, new routing, different tables, changed buffer limits, or a genuine sequencing rewrite.
- Do not rebuild a patch just to tweak a value that could remain live.

### 4. Retain the full DSP graph

`build()` must leave the patch strongly owning every Python object the running
DSP chain needs.

- Store every table, trigger, envelope, generator, modulation source, effect
	input, and Pyo arithmetic result as a `self.<name>` attribute, declared as
	an annotation on the class. `finish()` retains every public Pyo object on
	the instance automatically; use `self.retain(...)` (or `finish(...,
	resources=(...))` for a `GatedVoice`) only for objects that never become
	attributes, e.g. a list of triggers.
- Never embed a Pyo constructor or arithmetic expression anonymously inside
	another Pyo constructor. For example, replace `TrigEnv(trigger,
	CosTable(...))`, `Biquad(Noise() * envelope, ...)`, and
	`Lorenz(pitch=speed * 1.3, ...)` with named table, source, product, and
	modulation attributes.
- Profile/configuration dictionaries must store plain data or factories, not
	already-instantiated Pyo objects. Construct only the selected profile's
	native objects; creating all variants and discarding the unused ones while
	audio is running can race the audio callback.
- Treat closure capture and transitive ownership by a downstream Pyo object as
	implementation details, not lifetime guarantees. Pyo arithmetic results do
	not hold their operands: `a * b` alone won't keep `a` or `b` alive.

Pyo native nodes can outlive their Python wrappers. If a wrapper is collected
while PortAudio/CoreAudio is processing its node, the process can fail with an
intermittent native `SIGSEGV` in frames such as `TrigEnv_readframes_i` and
`Server_process_buffers`; Python exception handling cannot catch that crash.

Before considering a builder complete, audit its graph from sources to final
voice and account for each object in exactly one of these places:

- `Patch.voice`
- `Patch.sequencer`
- `Patch.resources`

Review this against the graph attributes `build()` assigns - there is no
automated structural check for it, since a base class's `retain()`/`envelope()`/
`schedule()`/`live()` calls and a style's own hook method (`tone()`, `voice_graph()`,
...) can split resource ownership across files in a way static analysis can't
reliably follow.

A rebuild runs `build()` again on the same instance; `Patch._reset()` stops
the previous graph if it is still playing and keeps it alive through its
fade. Always call `self._reset()` first in `build()`.

### 5. Keep timing/state explicit

Clocked and generative patches must preserve their sequence index, callback state, and random state when the same patch is updated.

- synthesis parameters usually remain live
- timing parameters often require custom setters or resubscription logic (`rate_param` already handles the clocked rate)
- keep sequence state (step counters, random state) on `self`, not reset by a parameter change
- do not treat timing as a normal live parameter unless the runtime is genuinely equivalent

### 6. Keep the patch module UI-free

Patch modules describe sound and controls; the Flet layer owns the UI.

- keep patch-specific ranges, labels, and descriptions in each `@Param` declaration
- expose the patch to a GUI by listing an instance in the project rack's `GroupController`s, not UI code in the patch module
- do not import Flet or build controls or slider wiring inside a patch module

## Quality bar

A patch is ready when it does all of the following:

- fits the nearest existing family or clearly justifies a new one
- exposes user-facing musical controls instead of raw DSP names
- updates live when the underlying topology is unchanged
- preserves the full graph lifetime with explicit ownership
- keeps timing behavior and state transitions deliberate
- follows the `@Param` / `build()` / `finish()` contract and plugs directly into a project rack's `GroupController`

If a concept belongs to the music skill rather than patch runtime discipline, move it there and keep this file focused on architecture and implementation rules.
