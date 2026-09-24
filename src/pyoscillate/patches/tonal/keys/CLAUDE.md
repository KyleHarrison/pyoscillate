# Keys

**Status: placeholder.** No patches exist in this directory yet. This file
sketches the sonic role so the family is discoverable. Fill in its
design sections (from sources) before implementing the first patch.

## Sonic function

Keys are a gated, polyphonic chordal voice with a struck attack and a bell-like decay, in the electric-piano family. Velocity changes brightness as well as level: a hard strike "barks", a soft one is round.

## Minimal architecture

trigger (velocity)
→ tine/tone source (FM or additive)
→ attack transient (bark) scaled by velocity
→ decaying amplitude envelope (no true sustain)
→ optional tremolo / chorus

## Boundaries

Unlike `pad/`, keys articulate every chord with a percussive attack and decay; unlike `pitched_percussion/bell`, the partials are close to harmonic so chords stay clear.

## Musical references

These point to the music-theory layer for decisions *around* this voice
(pattern, pitch material, role in the arrangement and mix). They do not
cover synthesis; the sections above stay authoritative for the DSP.

- `.claude/skills/music-theory/references/instrument-idiom/piano-keyboards.md` — voicing rules and comping
- `.claude/skills/music-theory/references/electronic-parts/chords-and-voicing.md` — "Keys and stabs — close voicing is fine"
