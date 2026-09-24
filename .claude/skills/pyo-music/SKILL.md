---
name: pyo-music
description: Use when a request needs music/sound-design reasoning that turns musical intent into sonic behaviour, DSP mechanism, parameter meaning, and user-facing patch descriptions before the exact Pyo implementation is chosen.
---

# Pyo Music

This skill is the bridge between the music-theory layer and the implementation layer. It does not replace either one.

## Entry points and routing

- Start with [../music-theory/SKILL.md](../music-theory/SKILL.md) for musical intent, genre, form, harmony, rhythm, and arrangement.
- Use [references/timbre-descriptors.md](./references/timbre-descriptors.md) when a brief or control label uses a perceptual word ("bright", "warm", "metallic", "punchy"). It maps each word to a perception, a measurable correlate, and several alternative mechanisms.
- Use [references/pyo-api-navigation.md](./references/pyo-api-navigation.md) to route from a synthesis idea into the authoritative Pyo docs in [references/pyo-api/](./references/pyo-api/).
- Use [../../../CLAUDE.md](../../../CLAUDE.md) for project architecture, `Patch` / `PatchDef` rules, `SliderSpec`, patch/runtime implementation, and the project-scaffolding workflow.

If a request is about new-project creation, app scaffolding, rack architecture, or patch implementation, do not keep that workflow inside this skill. That belongs in the project-level entry point: [../../../CLAUDE.md](../../../CLAUDE.md).

## Core responsibility

This skill answers:

> Given a musical intention, what should it sound like, what physical signal changes create that effect, what does the listener perceive, and how should the control or patch be described to a user?

It is not a second implementation framework and it does not duplicate the patch architecture in [../../../CLAUDE.md](../../../CLAUDE.md).

## Reasoning model

The central chain is:

```
MUSICAL INTENT
    ↓
SONIC INTENT
    ↓
DSP MECHANISM
    ↓
PERCEPTUAL AFFORDANCE
    ↓
MUSICAL CONSEQUENCE
    ↓
USER CONTROL
    ↓
PYO IMPLEMENTATION
```

Do not jump from "dark" or "metallic" straight to a Pyo object. First decide what the listener is meant to hear, then what physical change can create it, then which Pyo primitives can implement that change. [references/timbre-descriptors.md](./references/timbre-descriptors.md) covers that middle step for common descriptors.

## Parameter reasoning standard

For every exposed parameter, reason through this sequence:

```
Pyo parameter
    ↓
physical change
    ↓
perceptual effect
    ↓
musical consequence
    ↓
user-facing label
    ↓
user-facing help text
```

This is a reasoning framework, not a schema. It informs the language of the GUI and patch summary without replacing the existing `SliderSpec` architecture.

### 1. What physically changes?

Ask what the DSP parameter actually changes in the signal chain:

- oscillator frequency
- filter cutoff or resonance
- modulation depth
- envelope attack or release
- reverb damping or density
- amplitude or drive
- modulation rate
- stereo spread or panning

This is where the Pyo API remains authoritative.

### 2. What does the listener perceive?

Translate that signal change into perceptual language:

- filter frequency: darker ↔ brighter, closed ↔ open, muted ↔ present
- FM index: simple ↔ spectrally complex, pure ↔ bright/metallic/harsh depending on ratio, register, and carrier
- attack: immediate ↔ gradual, punchy ↔ soft/swelling
- reverb amount: dry/close ↔ spacious/distant, tight ↔ diffuse
- kick body amplitude: lighter ↔ fuller/heavier

For the full descriptor vocabulary, use [references/timbre-descriptors.md](./references/timbre-descriptors.md). Each entry gives the measurable correlate (centroid, envelope, pitch stability, and so on) to name in the help text and to check when rendering. It also lists the descriptors a word is commonly confused with.

### 3. What musical outcome can that support?

Translate the perceptual effect into musical role:

- brighter → presence, lead, articulation, energetic texture
- darker → subbed, atmospheric bed, background layer
- longer attack → gentle swell, pad, ambient onset
- short attack → pluck, percussion, rhythmic articulation
- stronger rhythmic modulation → pulse, groove, movement

This is contextual and not deterministic.

## Do not overclaim mappings

Perceptual mappings depend on context.

Examples:

- increasing FM index does not always mean "brighter"; it may sound rich, buzzy, metallic, harsh, or unstable depending on the carrier, ratio, register, envelope, and whether it is heard as a pitched tone or texture
- increasing reverb does not simply mean "more space"; it can change distance, density, sustain, clarity, and rhythmic definition
- shorter attack can sharpen articulation or create brittleness depending on the rest of the signal chain

Use this shape:

```
physical change
    ↓
likely perceptual effect
    ↓
depending on context
    ↓
possible musical use
```

## Modulation and timescale

Modulation is a relationship, not a class:

```
source + destination + rate/timescale + depth
    ↓
perceptual result
    ↓
musical affordance
```

Examples:

- LFO → pitch → vibrato / pitch movement
- LFO → amplitude → tremolo / pulsing
- LFO → filter cutoff → wah / brightness sweep
- LFO → stereo position → spatial motion
- envelope → amplitude → articulation
- envelope → filter cutoff → brightness contour over time

Timescale matters too:

- very slow modulation → evolution, drift, breathing
- note-rate modulation → movement, contour, articulation
- rhythmic modulation → pulse, groove, texture
- audio-rate modulation → timbral transformation

## Patch-level summary reasoning

At patch level, the useful question is:

> What musical or perceptual role does this patch contribute when it is enabled?

Prefer summaries such as:

- "Four-on-the-floor foundation."
- "Slow-moving atmospheric texture."
- "Bright, expressive melodic lead."
- "Warm sustained harmonic bed."
- "Rhythmic spectral movement."

Avoid implementation-led summaries such as:

- "Kick using an oscillator, envelope, and saturation."
- "Pad with filtered FM and reverb."

The patch reasoning chain is:

```
patch architecture
    ↓
sonic character
    ↓
musical role
    ↓
short user-facing summary
```

## User-facing control descriptions

Prefer the perceptual or musical affordance over the raw DSP name.

Examples:

- raw: "Level" / "Kick body level."
- better: label = "Body" ; help = "Controls the fullness and weight of the kick."

- raw: "Cutoff" / "Filter cutoff frequency."
- better: label = "Brightness" ; help = "Moves the sound from dark and muted to bright and open."

The choice of wording should come from the actual patch and the real musical role it serves.

## Relationship to the other layers

### [../music-theory/SKILL.md](../music-theory/SKILL.md)

This is the authority for musical intent: genre conventions, harmony, rhythm, form, arrangement, and composition. It tells the agent what the piece is meant to do musically.

### [references/pyo-api-navigation.md](./references/pyo-api-navigation.md) and [references/pyo-api/](./references/pyo-api/)

These are the authority for DSP truth: the actual Pyo objects, constructor signatures, and technical behaviour.

### [../../../CLAUDE.md](../../../CLAUDE.md)

This is the authority for project architecture and implementation rules:

- patch module structure
- `PARAMETERS`
- `SliderSpec`
- `Patch` / `PatchDef`
- widget implementation
- runtime safety and graph ownership
- rack architecture
- new-project scaffolding workflow

This skill should not repeat those rules.

## Project-level workflow entry point

The project-scaffolding path is not owned by this skill. For new project creation, use the workflow in [../../../CLAUDE.md](../../../CLAUDE.md), especially its "New project workflow" section.

That workflow is the correct location for:

- app + rack generation
- project folder layout
- patch family reuse vs. new-module creation
- notebook and preset structure
- project README planning

This skill simply provides the musical and sonic reasoning that feeds that project-level workflow.

## Minimal working pattern

For a new request, do this in order:

1. Start with the musical idea and its role.
2. Turn it into sonic intent: what should the listener hear?
3. Identify the real DSP mechanism that can produce it.
4. Ask what physically changes and what perceptually follows.
5. Map that to the relevant musical consequence.
6. Choose user-facing names and help text.
7. Only then implement with the actual Pyo objects and parameters.

This keeps the agent from collapsing the creative chain too early and from treating the Pyo API as if it were the musical meaning itself.

## Examples of the intended reasoning

### FM example

- physical change: increasing FM index increases the amount of carrier/modulator interaction
- perceptual effect: more spectral complexity, often brighter or more metallic depending on ratio and register
- musical consequence: can support a lead, a sharper transient, or a more unstable textural layer
- user-facing language: "Brightness" or "Complexity" depending on the patch
- not universal: the same change can sound rich, harsh, or smooth depending on context

### Modulation example

- source: LFO
- destination: filter cutoff
- rate: slow vs. note-rate vs. rhythmic
- perceptual effect: subtle movement, wobble, spectral wash, or pulsing brightness
- musical consequence: motion, breathing, groove, texture, or accent
- user-facing label: "Motion" or "Brightness" depending on the role

### Envelope example

- physical change: longer attack and slower release
- perceptual effect: softer onset and more bloom
- musical consequence: pad, atmospheric bed, long swell
- short attack would instead imply pluck, rhythmic articulation, or percussive bite

### Reverb example

- physical change: more decay or density
- perceptual effect: more distance and diffusion, but possible loss of clarity if overdone
- musical consequence: space, ambience, or wash
- user-facing wording should describe the resulting musical experience rather than the DSP object name

### Patch-summary example

- "Four-on-the-floor foundation."
- "Slow-moving atmospheric texture."
- "Bright, expressive melodic lead."

These descriptions answer what the patch contributes to the music, not what DSP building blocks were used.
