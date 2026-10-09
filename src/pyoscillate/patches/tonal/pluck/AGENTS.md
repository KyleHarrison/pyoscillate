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

Karplus-Strong string (`string.py`, the base of `guitar.py`, `folk.py`, `harp.py`, `sitar.py` and `bass/standup.py`):
    low-passed noise burst → comb for the pick position → `Waveguide` (a tuned delay line with a low-pass in its feedback loop) → a style's voice stage. The loop low-pass shaves the highs on every trip, so each note starts bright and mellows as it rings, which a fixed-spectrum oscillator with an envelope cannot do. A round-robin bank of strings keeps a ringing note from being retuned when the next is struck.
    An instrument is data and a voice stage: how hard the pluck is (`pluck_time`, Brightness), where it lands (Pluck position), how many strings sound for each note (`courses`: a mandolin's unison pairs, a kora's octave pairs), how long they ring (Sustain) and what follows. A hollow body is the shared `Body` mixin (`common.py`: resonators at `body_modes`); an electric guitar's amp is a waveshaper and cabinet; a sitar adds a buzzing bridge and sympathetic strings tuned to the chord's root and fifth. A hook phrase plays chord tones; a bass line plays semitones above the chord root.

## What NOT to assume

`guitar.py` is a plucked-string model, not a full guitar: it has no fretting, string-to-string coupling, pick noise on the body, or per-note dynamics. The acoustic body is three fixed resonances and the amp is one waveshaper with a tone filter, so treat both as character, not as measured instruments. Pyo's `Waveguide` fixes the loop damping to its `dur`, so Brightness shapes the pluck, not how fast the highs die; that rate follows Sustain.

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
