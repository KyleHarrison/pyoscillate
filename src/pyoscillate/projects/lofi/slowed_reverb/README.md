# Slowed Reverb

A dark, **slowed-and-reverbed** sibling to [`lofi/boom_bap`](../boom_bap/README.md)
— not an edit to that 80 BPM boom-bap rack, but a different mood built from
the same lofi family: a slow, half-time drag, a bass-dominant balance, and a
mix soaked in a long, breathing reverb tail, now anchored by a restrained
brushed groove. Grounded in reference-track analysis (tempo/beat tracking, chroma,
spectral centroid/rolloff/flatness, band-limited bass pitch tracking on
30-250 Hz) of a "slowed + reverb" remix — see
[docs/todos/slowed-reverb-rack.md](../../../../../docs/todos/slowed-reverb-rack.md)
for the full extracted data. Per that data and the root
[CLAUDE.md](../../../../../CLAUDE.md)'s foundational principle, this is
grounding, not a spec to copy: nothing here reproduces the reference's
arrangement note-for-note.

## Musical brief

- **Tempo/feel:** felt tempo ~61 BPM (the beat tracker's ~123 BPM read as a
  half-time "slowed" mix); 4/4; a sparse, brushed MPC-style swing pocket
  rather than a conventional full drum groove.
- **Harmony/mode:** E Phrygian (chroma peaks at E, G, A; the bass's
  dominant F1 note is Phrygian's characteristic ♭2 above the E tonic) — see
  `.claude/skills/music-theory/references/harmony/modal-harmony.md`'s
  "Phrygian (♭2 in a minor frame)". The centre is established by repetition
  and a held tonic beneath the lead group's C-major progression (see
  "Shared harmony and tempo" below).
- **Density:** bass and atmosphere remain dominant, with a selectable
  sustained lead, an independent upper-register chord-tone hook, and quiet
  kick/hat pulse. The added parts create audible mid/high harmony without
  turning the arrangement into a full band.
- **Bass:** hovers on the E1 tonic with stepwise F1/G1/A1 neighbour motion
  (not chord-following), a clean near-sine timbre (bass-band spectral
  flatness 0.0036, centroid ~151 Hz — minimal harmonic content, no growl or
  808 saturation), and a soft attack/release shaped by the mix's reverb
  tail rather than a plucky envelope.
- **Reference timbre:** heavily dark — spectral centroid ~513 Hz, rolloff
  ~853 Hz across the full mix. Low spectral flatness (0.0037) means
  tonal/pad-like content, not noise. The upper hook and soft hat deliberately
  add mid/high definition while keeping the bass and wash in front.
- **Dynamics:** moderate, breathing swell (RMS mean 0.134, std 0.084) rather
  than sharp transients — consistent with a long reverb tail slowly surging
  around soft, restrained rhythmic accents.

## Concept-to-patch mapping

| Concept | Patch | Reuse / extend / new |
|---|---|---|
| Bass — hovers on tonic with stepwise neighbour motion, clean near-sine tone and a soft, reverb-shaped envelope | `tonal/bass` (`BassHover`) | **Reuse, re-tuned.** Keeps the chosen finished-preset cutoff, space, tail darkness, distance, breath, rate and output level as the rack's starting values. |
| Mix-wide dark, reverberant, breathing character | `tonal/drone` (`SoundscapeWash`) | **Reuse, re-tuned.** The finished values bring out audible chorus and delay while shortening and brightening the reverb tail. Slow pitch wander remains the bed's independent movement; a quiet kick sidechain adds a small rhythmic dip. Its `on_evolve` variation gently opens the chorus over long sections. |
| Sustained harmonic lead — selectable strings or FM keys | `tonal/strings` (`Strings`), `tonal/keys` (`Keys`) | **Reuse, re-tuned.** Both follow the shared `Dm9-G13-Cmaj9-Am9` vamp, retain the finished preset's registers, tone and levels, and can coexist with the independent hook. |
| Upper harmony — sparse, articulated chord-tone figure around E4-E5 | `tonal/pluck` (`PluckHook`) | **New style in the existing placeholder family.** A fast FM pluck follows the rack chord roots and diatonic triad qualities, above the bass and wash. Its clocked sparse/full pattern rotates over long sections. |
| Pulse — low kick and soft swung high-hat with restrained ghost notes | `drums/kick` (`KickLofi`), `drums/hat` (`GrooveLofi`) | **Reuse, re-timed and softened.** Separate groups let kick and hat play together; both retain their proven lofi swing patterns at half density and gain a subtle fuller-pattern evolution. No snare is added. |
| Texture — dust/hiss under the reverb tail | `texture/noise` (`NoiseDust`) | **Reuse, re-tuned.** The finished preset's brighter, deeper, slightly louder dust values remain restrained by its patch output level. |
| Section arrival | Rack `Lift` macro | **Reuse.** One control raises chorus depth, hook brightness and lead presence together; long bar-count evolution provides slower automatic variation. |
| Shared harmony/tempo | `rack.py` | `SlowedReverbRack.bpm = 61`; C-major `Dm9-G13-Cmaj9-Am9` harmony for strings, keys and hook, heard against the E-Phrygian bass centre. |

## Shared harmony and tempo

`SlowedReverbRack.bpm = 61` is the felt half-time tempo. `Strings`, `Keys` and
`PluckHook` follow the same C-major `Dm9-G13-Cmaj9-Am9` progression. The hook
voices the chord triads an octave above their roots, making the harmony
legible in the middle and upper registers. `BassHover` remains independent,
hovering on `ROOT_NOTE = notes.E1` with its E-F-G-A neighbour-tone pattern,
while `SoundscapeWash` holds `notes.E2` beneath the progression. Enable the
kick before the pad so its sidechain can resolve the source when the wash
builds.

## What this rack does not attempt

- **A literal reproduction of the reference's arrangement.** The extracted
  data (tempo, mode, bass register/rhythm, mix-wide spectral shape) grounds
  original synthesis decisions; it is not a transcription target.
- **A rack-level master effects bus.** Pyo racks in this project have no
  shared post-processing chain (see `projects/base.py`), so the "mix-wide"
  dark/reverberant character is a per-patch decision (bass + pad + hook), not a
  single shared `Lowpass`/`Freeverb` insert. A future rack-level effects bus
  would let this be expressed once instead of per patch.
