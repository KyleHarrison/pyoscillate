# Shaker

**Status: placeholder.** No patches exist in this directory yet. This file
sketches the sonic role so the family is discoverable. Fill in its
design sections (from sources) before implementing the first patch.

## Sonic function

A shaker is a very short, bright burst of noise played in dense, even subdivisions. Its identity is the grain of many tiny impacts smeared into one hit, and it lives in the groove's upper layer, filling the gaps between hats rather than marking the beat.

## Minimal architecture

trigger
→ noise source
→ high-pass / band-pass colour filter
→ very short envelope (optionally a soft attack for a "shh" rather than a click)
→ output

## Boundaries

Unlike `hat/`, the shaker has no metallic partials and rarely a long open tail; its expressive axis is attack softness and colour rather than open/closed decay. If a design grows metallic content, it belongs in `hat/`.

## Musical references

These point to the music-theory layer for decisions *around* this voice
(pattern, pitch material, role in the arrangement and mix). They do not
cover synthesis; the sections above stay authoritative for the DSP.

- `.claude/skills/music-theory/references/instrument-idiom/drums-percussion.md` — "Percussion layers" (what a shaker adds to a kit)
- `.claude/skills/music-theory/references/electronic-parts/drums-and-rhythm.md` — velocity accents and swing, which make or break a 16th-note shaker
