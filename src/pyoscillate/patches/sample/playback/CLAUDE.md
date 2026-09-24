# Sample playback

**Status: placeholder.** No patches exist in this directory yet. This file
sketches the sonic role so the family is discoverable. Fill in its
design sections (from sources) before implementing the first patch.

## Sonic function

A sample-playback voice triggers recorded audio. Its musical controls are where in the file it starts, how fast it plays (which also changes pitch), and how long it lasts. The material, not the synthesis, supplies the timbre.

## Minimal architecture

trigger
→ buffer read (start position, rate)
→ amplitude envelope / end-of-buffer stop
→ output

## Boundaries

If the sample is a drum loop cut into slices, use `sample/breakbeat`. If it is read as many tiny overlapping grains, use `sample/grains`.

## Musical references

These point to the music-theory layer for decisions *around* this voice
(pattern, pitch material, role in the arrangement and mix). They do not
cover synthesis; the sections above stay authoritative for the DSP.

- `.claude/skills/music-theory/references/research/style-reference-and-copyright.md` — using sampled material responsibly
