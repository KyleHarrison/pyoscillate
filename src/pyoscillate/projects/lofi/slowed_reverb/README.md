# Slowed Reverb

A dark, **slowed-and-reverbed** sibling to [`lofi/boom_bap`](../boom_bap/README.md)
— not an edit to that 80 BPM boom-bap rack, but a different mood built from
the same lofi family: a slow, half-time drag, a bass-dominant balance, and a
mix soaked in a long, breathing reverb tail rather than a conventional
groove. Grounded in reference-track analysis (tempo/beat tracking, chroma,
spectral centroid/rolloff/flatness, band-limited bass pitch tracking on
30-250 Hz) of a "slowed + reverb" remix — see
[docs/todos/slowed-reverb-rack.md](../../../../../docs/todos/slowed-reverb-rack.md)
for the full extracted data. Per that data and the root
[CLAUDE.md](../../../../../CLAUDE.md)'s foundational principle, this is
grounding, not a spec to copy: nothing here reproduces the reference's
arrangement note-for-note.

## Musical brief

- **Tempo/feel:** felt tempo ~61 BPM (the beat tracker's ~123 BPM read as a
  half-time "slowed" mix); 4/4; a steady, near-beat-synchronous pulse rather
  than a swung or syncopated groove.
- **Harmony/mode:** E Phrygian (chroma peaks at E, G, A; the bass's
  dominant F1 note is Phrygian's characteristic ♭2 above the E tonic) — see
  `.claude/skills/music-theory/references/harmony/modal-harmony.md`'s
  "Phrygian (♭2 in a minor frame)". The centre is established by repetition
  and a held tonic, not a cadence, so the rack has no `Harmony`
  chord-progression object (see "Shared harmony and tempo" below).
- **Density:** very sparse instrumentation. The reference's bass carries
  ~87% of total RMS — this is a bass-and-atmosphere piece, not a full band;
  adding a conventional drum kit or comping instrument on top would
  contradict the reference's own balance, so this rack deliberately doesn't
  reach for `boom_bap`'s drums/keys/strings roster.
- **Bass:** hovers on the E1 tonic with stepwise F1/G1/A1 neighbour motion
  (not chord-following), a clean near-sine timbre (bass-band spectral
  flatness 0.0036, centroid ~151 Hz — minimal harmonic content, no growl or
  808 saturation), and a soft attack/release shaped by the mix's reverb
  tail rather than a plucky envelope.
- **Mix-wide timbre:** heavily dark — spectral centroid ~513 Hz, rolloff
  ~853 Hz across the full mix. Low spectral flatness (0.0037) means
  tonal/pad-like content, not noise.
- **Dynamics:** moderate, breathing swell (RMS mean 0.134, std 0.084) rather
  than punchy transients — consistent with a long reverb tail slowly
  surging rather than discrete hits.

## Concept-to-patch mapping

| Concept | Patch | Reuse / extend / new |
|---|---|---|
| Bass — hovers on tonic with stepwise neighbour motion, clean near-sine tone, ~87% of the mix's energy, soft/reverb-shaped envelope | `tonal/bass`, new style `BassHover` (`hover.py`) | **Extend.** The existing `groove.GrooveBass` styles are all chord-following (`needs_harmony=True`) and dry, left for the rack to treat externally — neither fits a fixed-tonic voice with its own long reverb tail. `Bass.build_voice` gained a `voice_output()` hook (same pattern as `Kick`/`Groove`'s own post-processing hook) so a style can add effects after the shared oscillator/filter chain instead of every style needing its own copy of that graph. `BassHover` uses the shared graph via a new profile (`profiles.HOVER`: a four-bar, steady 8th-note pulse that steps E→F→G→A once per bar) and overrides `voice_output()` to add its own `Freeverb` plus a slow, four-bar `Sine`-modulated amplitude swell ("Breath") for the reference's breathing dynamics. |
| Mix-wide dark, reverberant, breathing character | `tonal/drone` (`SoundscapeWash`) | **Reuse, re-tuned.** There is no rack-level master bus (`projects/base.py`'s `Rack` has no shared effects chain — see the todo's "reason through pyo-music, don't reach for a single shared `Lowpass`+`Freeverb`"), so the "mix-wide" character is realized as a per-patch decision instead: `BassHover`'s own reverb/breath (above) carries most of it, since the bass is ~87% of the mix's energy, and `SoundscapeWash` (already built for exactly this — chorus/reverb/delay smear, see `tonal/drone/wash.py`'s docstring) supplies a quiet, static, dark pad bed underneath at a low register (`root_freq=E2`) and a long, damped reverb (`reverb_size=0.92`, `reverb_damp=0.65`). Its own slow `Rossler` pitch wander already reads as gentle breathing without any further change. |
| Texture — quiet dust/hiss under the reverb tail, continuous with the `lofi` family's aesthetic | `texture/noise` (`NoiseDust`) | **Reuse, re-tuned.** Same style `boom_bap` already uses for its vinyl-dust bed; darkened further (`brightness=700`, up from its own default 3200) to sit under this brief's ~850 Hz mix-wide rolloff, and quieted (`level=0.12`) since this mix has almost none of its energy outside the bass. |
| Drums, comping/lead instrument | — | **Deliberately not mapped.** The reference has no evidence of a separate drum or chordal-comping layer carrying meaningful energy (RMS is ~87% bass); adding `boom_bap`'s kick/snare/hat or keys/strings roster here would be reaching for "lofi = drums + chords" out of habit rather than following the data — see the root CLAUDE.md's foundational principle and the todo's "not just add a lowpass and call it lofi." |
| Shared harmony/tempo | `rack.py` | `SlowedReverbRack.bpm = 61`; no `Harmony` object (see below). |

## Shared harmony and tempo

`SlowedReverbRack.bpm = 61` is the felt half-time tempo. Unlike `boom_bap`,
this rack sets no `Harmony` (`Rack.harmony` stays `None`): neither patch
follows a chord progression — `BassHover` hovers on a fixed `root_freq`
(`ROOT_NOTE = notes.E1` in `rack.py`) with its own bar-by-bar neighbour-tone
pattern (`profiles.HOVER`), and `SoundscapeWash` holds one static register
(`notes.E2`). The E Phrygian centre is instead a compositional constant
(`ROOT_NOTE`) both patches' root frequencies are chosen around, documented
here rather than encoded as a `Harmony(key=..., progression=...)` object,
since there is no chord-following voice for that object to drive.

## What this rack does not attempt

- **A literal reproduction of the reference's arrangement.** The extracted
  data (tempo, mode, bass register/rhythm, mix-wide spectral shape) grounds
  original synthesis decisions; it is not a transcription target.
- **A rack-level master effects bus.** Pyo racks in this project have no
  shared post-processing chain (see `projects/base.py`), so the "mix-wide"
  dark/reverberant character is a per-patch decision (bass + pad), not a
  single shared `Lowpass`/`Freeverb` insert. A future rack-level effects bus
  would let this be expressed once instead of per patch.
