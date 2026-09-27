# Acid bass

**Status: placeholder.** No patches exist in this directory yet. This file
sketches the sonic role so the family is discoverable. Fill in its
design sections (from sources) before implementing the first patch.

## Sonic function

An acid bass is a gated, monophonic sequence line whose character comes from a resonant low-pass filter swept by a per-note envelope. Accent and slide shape the phrasing; the filter, not the pitch, carries most of the expression.

## Minimal architecture

trigger (+ accent, slide flags)
→ saw or square oscillator with glide
→ resonant low-pass
    ↑ filter envelope (depth and decay; accent deepens and shortens it)
→ amplitude envelope
→ optional overdrive

## Boundaries

The shared `tonal/bass` core uses a fixed or LFO-swept low-pass; this family exists because a per-note filter envelope with accent/slide is a different topology and control vocabulary.

## Musical references

These point to the music-theory layer for decisions *around* this voice
(pattern, pitch material, role in the arrangement and mix). They do not
cover synthesis; the sections above stay authoritative for the DSP.

- `.claude/skills/music-theory/references/electronic-parts/bass-lines.md` — "Driving (techno)" and "Filter as expression"
- `.claude/skills/music-theory/references/genres/electronic-edm.md` — acid house / techno context
