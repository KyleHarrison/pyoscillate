# Riser

**Status: placeholder.** No patches exist in this directory yet. This file
sketches the sonic role so the family is discoverable. Fill in its
design sections (from sources) before implementing the first patch.

## Sonic function

A riser is a one-shot gesture that builds tension into a section change: pitch, brightness, level and often noise content all climb over a set duration, usually one to several bars, and stop at the downbeat.

## Minimal architecture

trigger (timed to land on a downbeat)
→ rising source (pitch sweep and/or noise)
→ rising filter cutoff
→ rising level
→ optional reverb / delay tail

## Boundaries

A riser marks form, not groove, so it is not a drum. The duration should be set in bars from the tempo, not in free seconds.

## Musical references

These point to the music-theory layer for decisions *around* this voice
(pattern, pitch material, role in the arrangement and mix). They do not
cover synthesis; the sections above stay authoritative for the DSP.

- `.claude/skills/music-theory/references/form/narrative-and-transitions.md` — build-ups and transitions
- `.claude/skills/music-theory/references/production-aware/energy-and-dynamics.md` — energy curves, build-ups and drops
