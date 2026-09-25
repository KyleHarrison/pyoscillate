# Patch architecture

This directory is organized by patch type — one subdirectory per sonic/musical
role (a bass family, a kick family, a drone family, and so on), never per
project. This file stays deliberately free of hard references to specific
modules: implementations move, get renamed, and get replaced as the patch set
grows, so citing one file as "the" canonical example just goes stale. Treat
this file as the operating guide for the contract every patch must satisfy,
not as an index of example code.

## Read these first

- `.claude/skills/pyo-music/SKILL.md` — musical intent, synthesis strategy, and choice of Pyo objects
- The nested `CLAUDE.md` inside the patch-type directory you're working in — the concrete, concept-level authority for that sonic role (its sonic function, minimal architecture, and design alternatives)
- The other modules already living in that same directory — read them as working examples of the contract below, not this file

The goal is simple: musical reasoning is handled by the skill, the sonic concept for a given patch type is handled by that directory's own instruction file, and this file only covers the shared implementation/runtime contract every patch must follow.

## Directory model

- Each patch-type directory is self-contained: its own `CLAUDE.md` (sonic concept, described abstractly) plus one or more implementation modules (concrete builders/profiles for that concept).
- Before creating a new directory, check whether an existing one already covers the musical role you need and extend it instead.
- When a patch-type directory's `CLAUDE.md` is still empty, treat the existing modules in that directory as the working reference for style and shape until it is filled in — do not backfill this file with citations to fill that gap.

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
`CLAUDE.md` marked "Status: placeholder", but no patches yet. They record
roles a complete electronic toolkit needs. When you implement the first patch
in one, fill in its `CLAUDE.md` from sources first, then drop the placeholder
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

**Class-based is the contract**: a module defines one or more `Patch`
subclasses - optionally under a directory-level base that factors out real
shared behavior for that archetype (e.g. `pyoscillate.patches.common.GatedVoice`
for the trigger/envelope/scheduling shape every gated voice shares -
`drums.base.DrumVoice` is just that base's name within the drums family - or
`pyoscillate.patches.common.ContinuousVoice` for an ungated, free-running
voice's `live()` control shape). A project rack lists an instance of the
class directly (grouped by `PatchGroupDef`, no separate wrapper);
`name`/`title`/`summary`/`sidechain` all default from the instance itself
(its class name, docstring, and `Patch.__init__` args) rather than being
restated at the call site - pass `name=`/`title=`/`summary=`/`sidechain=` to
the constructor only when the default isn't the right rack key, UI copy, or
duck target. See `drums/kick/kick.py` (`Kick` / `KickRound` / `KickPunch` /
`KickSoft`) for the worked example, and
[docs/concepts/patch-lifecycle.md](../../../docs/concepts/patch-lifecycle.md)
for why it's shaped this way.

Each parameter is one `@Param(min, max, step, default, label, help)`
decorating a method named after it; the method body is the live control
(`self.node.attr = f(value)`). `self.<name>` is the current value, and
assigning it runs the control once the patch is built. `build()` takes no
per-parameter kwargs, constructs nodes with neutral values, and ends with
`return self.finish(voice)`, which runs every control once - so never repeat
a parameter's mapping inside `build()`. A style that needs a different
default or range redeclares only that parameter:
`punch = Kick.punch.replace(default=1.4)`. Unmigrated modules still use a
`PARAMETERS` tuple and a `controls` dict; migrate them to this shape when
you touch them.

Every patch module is class-based; there is no function-based fallback contract. When a style's graph genuinely differs from its siblings (not just profile data), factor the shared build steps into the family's base class and give each style its own hook method to override - see `pyoscillate.patches.tonal.bass.fm.fm`'s `FmBass.tone()` for the worked example.

Do not duplicate boilerplate in this file. Copy the structure from the actual modules that already work.

## Design rules

### 1. Extend existing families before creating new files

Before adding a new module, look for a neighboring patch with the same musical role.

Prefer:

- extending an existing patch family
- adding optional parameters to an existing builder
- using `make_builder(profile)` (function-based) or a subclass per style
  variant (class-based) when the signal graph and control intent are the
  same but fixed profile data differs - a subclass is also the right call
  when a variant needs genuinely different behavior, not just different
  profile data, since class attributes alone can't express that

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
`utility/notes` (`notes.A1`, not `55`). Continuous detune belongs in its own
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
	the instance automatically; use `self.retain(...)` only for objects that
	never become attributes (e.g. a list of triggers). Unmigrated modules that
	still use named locals must pass them all in `finish(..., resources=(...))`.
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
- timing parameters often require custom setters or resubscription logic
- do not treat timing as a normal live parameter unless the runtime is genuinely equivalent

### 6. Keep the patch module UI-free

Patch modules describe sound and controls; the Flet layer owns the UI.

- keep patch-specific ranges, labels, and descriptions in each `@Param` declaration
- expose the patch to a GUI by listing an instance in the project rack's `PatchGroupDef`s, not UI code in the patch module
- do not import Flet or build controls, preset handling, or slider wiring inside a patch module

## Quality bar

A patch is ready when it does all of the following:

- fits the nearest existing family or clearly justifies a new one
- exposes user-facing musical controls instead of raw DSP names
- updates live when the underlying topology is unchanged
- preserves the full graph lifetime with explicit ownership
- keeps timing behavior and state transitions deliberate
- follows the `@Param` / `build()` / `finish()` contract and plugs directly into a project rack's `PatchGroupDef`

If a concept belongs to the music skill rather than patch runtime discipline, move it there and keep this file focused on architecture and implementation rules.
