# Click

**Status: placeholder.** No patches exist in this directory yet. This file
sketches the sonic role so the family is discoverable. Fill in its
design sections (from sources) before implementing the first patch.

## Sonic function

A click is a reference pulse for timing: a short, clearly audible tick that marks beats (and optionally accents the downbeat) without musical intent.

## Minimal architecture

clock tick
→ short sine burst + noise transient
→ accent on the downbeat
→ output

## Boundaries

`musical/clock_tick` is a musical texture that happens to use clock sounds; this is a functional metronome.

## Musical references

These point to the music-theory layer for decisions *around* this voice
(pattern, pitch material, role in the arrangement and mix). They do not
cover synthesis; the sections above stay authoritative for the DSP.

- `.claude/skills/music-theory/references/fundamentals/rhythm-meter.md` — meter and downbeat accent
