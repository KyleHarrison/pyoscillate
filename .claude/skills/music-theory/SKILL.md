---
name: music-theory
description: Use for music theory, composition, orchestration, genre, arrangement, production-aware musical decisions, and sonic ideation independent of a specific synthesis library.
---

# Music Theory

Use this skill for the musical and sonic reasoning layer of a request: harmony,
melody, rhythm, form, orchestration, arrangement, genre conventions,
production-aware decisions, reference-track analysis, and generative musical
ideas.

## Entry point check

If the request involves building, editing, or reasoning about a Pyo patch
(sound design, synthesis, code under `src/pyoscillate/patches/`) rather than
pure composition — stop here and load
[`../pyo-music/SKILL.md`](../pyo-music/SKILL.md) instead. It's the layer
that routes between this skill and the Pyo API and owns the full reasoning
chain; loading it first (rather than arriving here directly) avoids doubling
back later. This file intentionally has no knowledge of Pyo itself.

## Loading order

Start with `references/00-navigation.md`. It routes the request to the smallest
relevant set of theory references. Usually load one to three additional files;
do not broadly load the whole library.

For vague sonic requests, first decide the musical interpretation and the
synthesis-level behavior in musical terms: register, density, timescale,
harmonic versus noisy content, periodic versus stochastic movement, and whether
an event is gated or free-running. This skill does not document Pyo objects.

For reference-track requests, use the reference-track research guidance to
extract characteristics rather than reproducing a track's melody, lyrics,
riffs, samples, vocal identity, or signature production.

## Reference map

Start with [`references/00-navigation.md`](./references/00-navigation.md),
which routes a request to the smallest relevant set of files.

- [`references/fundamentals/`](./references/fundamentals/) for scales, rhythm, notation, and prosody
- [`references/harmony/`](./references/harmony/) for chords, progressions, voice leading, and modulation
- [`references/melody/`](./references/melody/) for contour, motifs, and phrase construction
- [`references/rhythm-groove/`](./references/rhythm-groove/) for groove, syncopation, and odd meters
- [`references/form/`](./references/form/) for song structure and transitions
- [`references/genres/`](./references/genres/) for genre conventions
- [`references/orchestration/`](./references/orchestration/) for register, texture, and density
- [`references/production-aware/`](./references/production-aware/) for mix-aware arrangement and dynamics
- [`references/research/`](./references/research/) for reference-track and style analysis
- [`references/creative-workflows/`](./references/creative-workflows/) for brainstorming and iterative collaboration
- [Asset lookup table](./references/00-navigation.md#cheatsheets--when-to-use-assets) for compact lookup tables and reusable templates in `assets/`
