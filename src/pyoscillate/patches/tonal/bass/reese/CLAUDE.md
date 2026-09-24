# Reese bass

**Status: placeholder.** No patches exist in this directory yet. This file
sketches the sonic role so the family is discoverable. Fill in its
design sections (from sources) before implementing the first patch.

## Sonic function

A Reese bass is a sustained low line made from several slightly detuned saws. Their beating produces a slow phasing, hollow-then-full movement that is the whole identity of the sound; the notes are often long and few.

## Minimal architecture

trigger/gate
→ 2–3 saw oscillators, slightly detuned
→ low-pass (static or slowly moving)
→ amplitude envelope with long sustain
→ optional saturation

## Boundaries

A Reese is still a gated bassline. If the detuned stack holds one pitch and never re-articulates, it is a drone (`tonal/drone`), not a Reese.

## Musical references

These point to the music-theory layer for decisions *around* this voice
(pattern, pitch material, role in the arrangement and mix). They do not
cover synthesis; the sections above stay authoritative for the DSP.

- `.claude/skills/music-theory/references/electronic-parts/bass-lines.md` — register and kick interaction
- `.claude/skills/music-theory/references/techniques/microtonal.md` — "Cents", for reasoning about detune and beating rate
- `.claude/skills/music-theory/references/genres/electronic-edm.md` — DnB / jungle context
