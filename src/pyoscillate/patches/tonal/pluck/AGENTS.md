# Pluck

## Sonic function

A pluck is a short, bright, articulated tone with a fast decay. Its identity is not just a short envelope; the important design idea is that the brightness decays over time while the body may remain audible for a shorter but still musical period.

## Minimal architecture

trigger
→ harmonic source
→ fast excitation or attack shaping
→ brightness contour
→ body decay
→ optional damping or resonant filter

## Brightness and decay

The key perceptual relationship is:

- quick attack
- strong initial brightness
- fast reduction in high-frequency content
- brief sustain of the resonant body

This can be created by an oscillator plus an envelope on a filter cutoff, by a short transient burst into a resonant network, or by a harmonic source with a rapidly decaying brightness component.

## Important design dimensions

- waveform choice: sine or triangle for softness; saw or square for bite
- brightness envelope: faster decay creates a more percussive pluck
- resonance or damping: controls the length of the body
- amount of attack transient: higher values add clarity or metallic bite
- reverb: can support space without extending the core note excessively

## Design alternatives

Gentle pluck:
    soft oscillator + short body + subtle bright transient

Guitar-like pluck:
    resonant body + stronger brightness decay + moderate attack

Electronic pluck:
    richer harmonic source + filter-envelope contour + clipped or saturated body

## What NOT to assume

A pluck is not just "a synth with a short envelope." The interesting part is the interaction of attack, brightness decay, and resonant body. That is what gives it a distinct plucked character instead of simply a short tone.

## Musical references

These point to the music-theory layer for decisions *around* this voice
(pattern, pitch material, role in the arrangement and mix). They do not
cover synthesis; the sections above stay authoritative for the DSP.

- `.claude/skills/music-theory/references/instrument-idiom/piano-keyboards.md` — "Broken-chord arpeggio", for arpeggiated pluck patterns
- `.claude/skills/music-theory/references/rhythm-groove/rhythmic-devices.md` — "Syncopation", since pluck lines often carry the off-beat motion
- `.claude/skills/music-theory/references/melody/melodic-construction.md` — for short melodic figures
- `.claude/skills/music-theory/assets/progressions-catalog.md` and `intervals-and-scale-formulas.md` (same folder) — for the chord and scale material the pluck outlines
- `.claude/skills/pyo-music/references/pitch-and-harmony-implementation.md` — when a pluck sounds chords rather than single notes
