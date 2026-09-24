# Breakbeat

**Status: placeholder.** No patches exist in this directory yet. This file
sketches the sonic role so the family is discoverable. Fill in its
design sections (from sources) before implementing the first patch.

## Sonic function

A breakbeat voice plays a recorded drum loop cut into equal slices and resequences them: reordering, stuttering, reversing and re-pitching slices to create new grooves from the same performance.

## Minimal architecture

buffer + slice grid (slices per bar)
→ clocked slice index sequence (negative = reversed)
→ per-slice rate
→ short fades at slice edges
→ output

## Boundaries

The musical logic (slice orders, genre tempos) lives in the music-theory layer; this family owns only slicing and playback.

## Musical references

These point to the music-theory layer for decisions *around* this voice
(pattern, pitch material, role in the arrangement and mix). They do not
cover synthesis; the sections above stay authoritative for the DSP.

- `.claude/skills/music-theory/references/electronic-parts/breakbeats.md` — slice counts, rearrangement techniques, genre applications
- `.claude/skills/music-theory/references/genres/electronic-edm.md` — jungle / DnB / breakbeat context
