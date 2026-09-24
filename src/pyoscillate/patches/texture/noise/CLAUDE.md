# Noise

**Status: placeholder.** No patches exist in this directory yet. This file
sketches the sonic role so the family is discoverable. Fill in its
design sections (from sources) before implementing the first patch.

## Sonic function

A filtered-noise layer is the simplest texture: a broadband source whose character is set entirely by filter type, cutoff and resonance, and whose movement comes from modulating those. It can be air, hiss, surf or wind depending on shaping.

## Minimal architecture

noise source (white / pink)
→ selectable low-, high- or band-pass
    ↑ slow modulation of cutoff / resonance
→ level
→ optional spatial treatment

## Boundaries

An ungated noise bed is texture. A gated noise sweep used to mark a section change belongs in `transition/`; a noise hit on the grid belongs in `drums/`.

## Musical references

These point to the music-theory layer for decisions *around* this voice
(pattern, pitch material, role in the arrangement and mix). They do not
cover synthesis; the sections above stay authoritative for the DSP.

- `.claude/skills/music-theory/references/orchestration/arrangement-density.md`
- `.claude/skills/music-theory/references/production-aware/arrangement-for-mix.md` — keeping hiss out of the vocal/lead band
