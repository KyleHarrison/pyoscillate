# Grains

**Status: placeholder.** No patches exist in this directory yet. This file
sketches the sonic role so the family is discoverable. Fill in its
design sections (from sources) before implementing the first patch.

## Sonic function

A granular sampler reads a recording as many short overlapping grains. Grain size and rate move the result from rhythmic stutter, through pitched buzz, to a smooth cloud; scanning position speed freezes or stretches the source.

## Minimal architecture

buffer
→ grain scheduler (rate, jitter)
→ grain reader (position, position speed, size, pitch)
→ grain window
→ stereo spread
→ output

## Boundaries

Grain clouds synthesized from oscillators or noise with no pitch centre are `texture/`; this family is for granulating recorded material.

## Musical references

These point to the music-theory layer for decisions *around* this voice
(pattern, pitch material, role in the arrangement and mix). They do not
cover synthesis; the sections above stay authoritative for the DSP.

- `.claude/skills/music-theory/references/techniques/20th-century-techniques.md` — "Spectralism" and "Aleatoric / chance music", for density and stochastic control
