# Strings

**Status: placeholder.** No patches exist in this directory yet. This file
sketches the sonic role so the family is discoverable. Fill in its
design sections (from sources) before implementing the first patch.

## Sonic function

A string ensemble is a sustained chordal voice imitating a section rather than a solo instrument: many slightly detuned voices, a bowed swell on the attack, and ensemble chorus that makes the chord shimmer.

## Minimal architecture

gate
→ several detuned saws per note
→ low-pass for warmth
→ slow attack / release envelope
→ ensemble chorus
→ optional reverb

## Boundaries

Closely related to `pad/` (string machines are where the classic pad came from). Keep it separate when the goal is a recognisable section sound — bowed attack, ensemble shimmer — rather than an evolving, breathing pad.

## Musical references

These point to the music-theory layer for decisions *around* this voice
(pattern, pitch material, role in the arrangement and mix). They do not
cover synthesis; the sections above stay authoritative for the DSP.

- `.claude/skills/music-theory/references/instrument-idiom/strings.md` — section writing and range
- `.claude/skills/music-theory/references/electronic-parts/chords-and-voicing.md` — open voicings and voice leading
- `.claude/skills/music-theory/references/orchestration/voicing-and-texture.md`
