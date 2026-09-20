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

- drums: kick, snare, clap, hat, cymbal, tom, percussion
- pitched percussion: bell
- tonal voices: bass, pluck, lead, pad, drone
- texture families: atmosphere, texture, soundscape

These answer: “How are those mechanisms combined to create a recognisable sound family?”

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

Every patch module should expose the same public interface:

- `PARAMETERS`: ordered `SliderSpec` values for the notebook controls
- `build(...) -> Patch`: creates the DSP graph and returns the live patch
- `widget(...)`: creates the standard control surface through `patch_widget(...)`

Do not duplicate boilerplate in this file. Copy the structure from the actual modules that already work.

## Design rules

### 1. Extend existing families before creating new files

Before adding a new module, look for a neighboring patch with the same musical role.

Prefer:

- extending an existing patch family
- adding optional parameters to an existing builder
- using `make_builder(profile)` when the signal graph and control intent are the same but fixed profile data differs

Create a new patch module only when the patch genuinely needs a new control surface, topology, or lifecycle.

### 2. Keep parameters musical, not technical

A slider should describe what the listener hears:

- `Brightness`, `Body`, `Punch`, `Warmth`, `Movement`, `Depth`, `Drive`, `Decay`, `Rate`

Avoid exposing low-level implementation names such as filter cutoff, oscillator gain, wet/dry amount, or coefficient values when a perceptual label is clearer.

The `help_text` should answer: “What will I hear if I move this slider?”

### 3. Parameter changes should usually be live

If a parameter can change without changing the graph topology, it should be exposed as a live Pyo control and updated through `Patch.controls`.

- `Patch.update(...)` is the standard runtime update path.
- Rebuilds are for structural choices only: new voice count, new routing, different tables, changed buffer limits, or a genuine sequencing rewrite.
- Do not rebuild a patch just to tweak a value that could remain live.

### 4. Retain the full DSP graph

`build()` must return a patch that strongly owns the Python objects needed by the running DSP chain.

- name tables, triggers, envelopes, generators, and arithmetic intermediates
- include graph-critical objects in `Patch(resources=(...))` when needed
- do not rely on anonymous constructor expressions to keep the graph alive

This is important because Pyo native nodes can outlive their Python wrappers and cause nondeterministic crashes when patches are updated or multiple instances are active.

### 5. Keep timing/state explicit

Clocked and generative patches must preserve their sequence index, callback state, and random state when the same patch is updated.

- synthesis parameters usually remain live
- timing parameters often require custom setters or resubscription logic
- do not treat timing as a normal live parameter unless the runtime is genuinely equivalent

### 6. Keep the notebook contract small

Patch modules should not manually reconstruct the same UI plumbing each time.

- use `patch_widget(...)` for the standard controls
- keep patch-specific ranges, labels, and descriptions in the patch module
- do not duplicate preset registration or `interactive_output` wiring

## Quality bar

A patch is ready when it does all of the following:

- fits the nearest existing family or clearly justifies a new one
- exposes user-facing musical controls instead of raw DSP names
- updates live when the underlying topology is unchanged
- preserves the full graph lifetime with explicit ownership
- keeps timing behavior and state transitions deliberate
- follows the standard `patch_widget` contract

If a concept belongs to the music skill rather than patch runtime discipline, move it there and keep this file focused on architecture and implementation rules.
