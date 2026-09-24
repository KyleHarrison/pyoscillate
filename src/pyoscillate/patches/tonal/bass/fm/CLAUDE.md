# FM bass

**Status: placeholder.** No patches exist in this directory yet. This file
sketches the sonic role so the family is discoverable. Fill in its
design sections (from sources) before implementing the first patch.

## Sonic function

An FM bass gets its harmonics from frequency modulation rather than filtering. The modulation index is the "growl" control: low index is round and sub-like, high index is buzzy and metallic. An index envelope makes each note bark then settle.

## Minimal architecture

trigger
→ modulator (ratio × note frequency)
    ↑ index envelope
→ carrier at note frequency
→ amplitude envelope
→ output

## Boundaries

Integer ratios keep the bass harmonic and tonal; non-integer ratios drift toward the bell family (`pitched_percussion/bell`) and lose pitch clarity in the low register.

## Musical references

These point to the music-theory layer for decisions *around* this voice
(pattern, pitch material, role in the arrangement and mix). They do not
cover synthesis; the sections above stay authoritative for the DSP.

- `.claude/skills/music-theory/references/electronic-parts/bass-lines.md` — movement and kick interaction
- `.claude/skills/music-theory/references/instrument-idiom/bass.md` — synth bass role
