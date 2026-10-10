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
    An instrument is data, shared controls with its own starting values, and a voice stage: how hard the pluck is (Hardness: the strike's length and how much of Brightness it lets through), where it lands (Pluck position), how loose the hand is (Dynamics, Looseness), whether it is damped (Mute), rocked (Vibrato) or scooped (Bend), how much of the pick is heard (Pick noise), how many strings sound for each note (`courses`: a mandolin's unison pairs, a kora's octave pairs, a 12-string's octaves), how long they ring (Sustain) and what follows. A hollow body is the shared `Body` mixin (`common.py`: resonators at `body_modes`, Body and Body size); an electric guitar's amp is a waveshaper, tremolo and cabinet; a sitar adds a buzzing bridge and sympathetic strings tuned to the chord's root and fifth. A hook phrase plays chord tones; a bass line plays semitones above the chord root.

## Every instrument is its own

A plucked instrument is never "the base with different constants". Every one must sound and feel different from every other, and the controls are how:

- **Own every shared control.** A style gives Hardness, Dynamics, Looseness, Pick noise, Vibrato, Sustain, Brightness and Pluck position a starting value chosen for that instrument (a banjo's hard, loose, clicky pick; a lute's soft, expressive fingertip; a dulcimer's felt hammers), and `click_freq` (the pitch of the pick's noise), the body and the register. Leaving a control at the base default needs a reason; no two instruments may start identically.
- **Add at least one signature control.** Each instrument exposes something only its kind of instrument has, as a `@Param` named by what you hear: a banjo's Twang, a mandolin's Spread and Doubling (the `Courses` mixin), a harp's and sitar's Sympathy and Sympathy ring (the `Sympathy` mixin), an electric guitar's Drive, Tone, Speaker and Tremolo, a sitar's Buzz and meend (Bend), a standup bass's Grit. A new instrument either reuses a mixin that fits it or adds its own control; a style with only shared controls is incomplete.
- **Put a repeatable idea in a mixin, not in two copies.** When two instruments need the same signature control (paired strings, unplayed strings that ring), it lives once on a mixin in `string.py` (`Courses`, `Sympathy`) or in `common.py` (`Body`), and each instrument sets its own starting value and, where its meaning differs, its own `help_text` (`doubling = Courses.doubling.replace(help_text=...)`).
- **Make every control audible.** Each control has a test that measures the sound change it makes, and the family test refuses a style that starts like another or has no control of its own (`PluckedStringCharacterTests`).
- **Keep loudness neutral.** A control that moves a level (Hardness, Doubling, a saturating stage) is compensated so moving it changes the character, not the volume.

## What NOT to assume

`guitar.py` is a plucked-string model, not a full guitar: it has no fretting, string-to-string coupling, pick noise on the body, or per-note dynamics. The acoustic body is three fixed resonances and the amp is one waveshaper with a tone filter, so treat both as character, not as measured instruments. Pyo's `Waveguide` fixes the loop damping to its `dur`, so Brightness and Hardness shape the pluck, not how fast the highs die; that rate follows Sustain (and Mute, which shortens it). The pluck is a burst of noise, so Hardness changes how much of Brightness gets through and how much energy goes in, not a true pulse shape; Looseness drifts the note by a few cents and varies its level, not its timing; sympathetic strings are sharply tuned, so a drifting note rings them less.

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
