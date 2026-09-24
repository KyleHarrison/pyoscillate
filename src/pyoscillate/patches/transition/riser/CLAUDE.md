# Riser

## Sonic function

A riser is a one-shot gesture that builds tension into a section change. Pitch, brightness and level climb together over a set number of bars, then cut off on the downbeat. It works because every change points the same way. The ear follows the climb and expects it to resolve, and the downbeat is where it resolves. A riser that fades out before the downbeat, or keeps going past it, loses that effect.

## Minimal architecture

phrase clock (bars)
→ one ramp, 0 → 1 across the riser's length, dropping to 0 on the downbeat
→ curve (how late the energy arrives)
→ rising source (noise band, frequency shift or pitch)
→ low-pass opening towards Brightness
→ level following the same curve

One ramp drives every destination. Separate envelopes for pitch, filter and level would drift apart, and the rise would stop sounding like a single gesture.

## Timing

- The length is set in **bars**, from the tempo, never in free seconds. The riser starts `length` bars before the end of its phrase, so it always lands on the phrase downbeat.
- The phrase in the build-up reference is 8 or 16 bars long. A 4-bar riser in an 8-bar phrase is the "bars 5–8: add a riser synth" move. An 8-bar riser fills the whole phrase.
- The cut is part of the sound. The ramp falls to zero over a few milliseconds at the downbeat. That is short enough to read as an edge and long enough not to click.

## The curve

The shape of the ramp decides where the tension sits:

- a linear ramp spreads the climb evenly, so the middle of the build already sounds half-finished
- an exponential-feeling ramp (raised to a power above 1) holds back and then surges in the last beats, which is the usual EDM shape
- a power below 1 rises early and plateaus, which sounds like a swell more than a build

pyo's `Port` is a one-pole lag. It gives the plateau shape (fast at first, then slowing), and it can't restart from zero on each shot, so it is not used for the main ramp. `Linseg` (x05/05 break-point functions) restarts cleanly on every `play()`, and raising its output to a live power gives the curve.

## Rising sources

Each source climbs in a different way, so the same curve sounds different through each one:

- **Noise wash.** A band of noise whose centre climbs through the spectrum. It has no pitch, so it sits over any key. This is the "white noise wash" of bars 13–14 in the build-up reference.
- **Frequency shift.** A detuned saw chord is single-sideband shifted (Hilbert transform + quadrature sine, x06/07). The shift climbs from 0 Hz. Every partial moves up by the same number of Hz, so the harmonic spacing is lost as the sound rises: it goes from a chord to an inharmonic, metallic climb. The source pitch stays the same, but the sound climbs and gets more unstable, which reads as more tension than a plain pitch sweep.
- **Pitch climb.** The same detuned saw chord glides up by whole octaves. It is the most literal "rising pitch" riser and the most tonal. It clashes if the key changes at the drop.

Increasing:

- climb → how far the sound travels; half an octave is a nudge, three or four octaves is a full sweep
- brightness → how open the filter is at the peak; low keeps the riser behind the mix, high makes it the loudest thing before the drop
- surge → from an early swell to a late, sudden surge

## Design alternatives

Noise sweep:
    noise → band-pass climbing on the ramp → low-pass → level

Inharmonic climb:
    detuned saws → pre-filter → SSB frequency shift climbing on the ramp → low-pass → level

Pitch riser:
    detuned saws gliding up on the ramp → low-pass → level

Endless (Shepard/barber-pole) rise, not implemented yet:
    frequency shift inside a feedback delay, so each pass moves the spectrum up again and the rise has no audible top

Breath before the drop, not implemented yet:
    end the ramp one bar (or a beat) early, so the downbeat follows a moment of silence

## What NOT to assume

- Louder is not the same as more tension. Level alone just swells. The climb in pitch or brightness is what points the gesture at the downbeat.
- A frequency shift is not a pitch shift. It moves partials by a fixed number of Hz, not by a ratio, so the sound becomes inharmonic. That is the point of the shift source, not a defect.
- A reverb tail on the riser carries past the downbeat and blurs the cut. Put a tail on the drop instead, or keep it short.

## Boundaries

A riser marks form, not groove, so it is not a drum, and a snare roll that speeds up belongs in `drums/`. A continuous noise bed is `texture/noise`. A riser is gated: it is silent until the phrase clock reaches its start bar.

## Musical references

These point to the music-theory layer for decisions *around* this voice
(pattern, pitch material, role in the arrangement and mix). They do not
cover synthesis; the sections above stay authoritative for the DSP.

- `.claude/skills/music-theory/references/form/narrative-and-transitions.md` — build-ups and transitions
- `.claude/skills/music-theory/references/production-aware/energy-and-dynamics.md` — energy curves, build-ups and drops

## Sources

pyo examples x05/02–03 (linear and exponential ramps), x05/05 (break-point functions) and x06/07 (Hilbert transform), pyo 1.0.6 documentation; the build-up structure in `narrative-and-transitions.md`.
