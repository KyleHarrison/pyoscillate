# TODO: new rack — slowed/reverbed dark lofi, inspired by a reference track

Source: audio analysis of `WYS X Sweet Medicine - Spanish Castle (Slowed N
Reverb) [432Hz].mp3` (local file, not committed) on 2026-09-27 via `librosa`
(tempo/beat tracking, chroma, spectral centroid/rolloff/flatness, band-limited
pitch tracking on the 30-250 Hz range). This is a **new sibling project** to
`lofi` (see [src/pyoscillate/projects/lofi/](../../src/pyoscillate/projects/lofi/)),
not an edit to it — the existing lofi rack is an 80 BPM boom-bap brief; this
one is a slower, darker, reverb-soaked, bass-dominant mood pulled from the
reference. Follow [src/pyoscillate/projects/CLAUDE.md](../../src/pyoscillate/projects/CLAUDE.md)'s
8-step workflow in order.

**Not a clone.** The reference is a "slowed + reverb" remix of someone else's
track. Nothing here should aim to reproduce its arrangement note-for-note —
use the extracted numbers as sonic-reference grounding for an original brief,
same as reasoning from a verbal description, per the root
[CLAUDE.md](../../CLAUDE.md)'s foundational principle.

## Extracted reference data (grounding, not a spec to copy verbatim)

- **Tempo:** beat tracker reports ~123 BPM, but this is a "slowed" mix — likely
  half/double of the felt tempo. Treat the felt tempo as ~61-62 BPM (half-time),
  which matches the genre's characteristic drag.
- **Key/tonal centre:** chroma peaks at E, G, A → E minor / E Phrygian-ish
  centre.
- **Timbre:** spectral centroid ~513 Hz, rolloff ~853 Hz across the full mix —
  heavily low-passed, almost no top end. Whatever filtering strategy is chosen,
  the brief's overall ceiling should land in this range, not just "add a
  lowpass and call it lofi" (see root CLAUDE.md).
- **Density/texture:** spectral flatness 0.0037 (full mix) — tonal/pad-like,
  not noise-driven.
- **Dynamics:** RMS mean 0.134, std 0.084 — moderate, breathing dynamic
  swell, consistent with long reverb tails rather than punchy transients.
- **Bass (30-250 Hz band, isolated by bandpass, not a real stem):**
  - Register: median pitch ~48.5 Hz (G1), range 30-250 Hz.
  - Pitch content: dominant notes F1, A1, G1, E1 — hovers on E1 (tonic) with
    stepwise F/G/A neighbour motion, not chord-following.
  - Rhythm: onsets roughly every ~0.48s — a steady, near-beat-synchronous
    pulse, not syncopated.
  - Energy share: bass carries ~87% of the track's total RMS — a
    bass-dominant mix, unusually forward.
  - Timbre: bass-band spectral centroid ~151 Hz (close to fundamental),
    flatness 0.0036 — clean, sine-like, minimal harmonic/distortion content;
    no growl, no 808 saturation.
  - Envelope: soft attack/release, shaped by the same reverb tail as the rest
    of the mix rather than a plucky transient.

## Tasks

- [x] **Ground the brief.** Run this data through `.claude/skills/music-theory/SKILL.md`
      and `.claude/skills/pyo-music/SKILL.md` before naming any Pyo object —
      particularly for the bass (clean sine-like tone, dominant energy share,
      soft envelope) and the mix-wide dark/reverberant timbre. Decide a
      project name (e.g. something distinct from `lofi`/`deep_house`).
- [x] **Write the README first** at `src/pyoscillate/projects/{project_name}/README.md`
      per `projects/CLAUDE.md`'s "README before implementation" — musical
      brief (tempo ~61 BPM felt, E minor/Phrygian centre, dark/reverberant
      timbre, bass-dominant balance), concept-to-patch mapping table, shared
      harmony/tempo constants. Do this before any patch code.
- [x] **Bass patch decision.** Check `tonal/bass`'s existing profiles/styles
      (`src/pyoscillate/patches/tonal/bass/`) for a clean, sine-like,
      soft-envelope, tonic-hovering profile before creating a new one — the
      existing lofi rack's `BassMuted`/`BassConversation` are thumpy and
      sparse, not necessarily this bass's near-sine, always-present character.
      Extend or add a new style per the mapping table, not both.
- [x] **Mix-wide dark/reverb character.** Decide the synthesis strategy for
      the ~500-850 Hz ceiling and long reverb tail as a rack-level effect
      chain or per-patch treatment — reason through pyo-music, don't reach
      for a single shared `Lowpass`+`Freeverb` without checking it matches the
      "breathing" dynamic (RMS std) noted above.
- [x] **Reuse pass.** Search existing patch families (drums, keys, strings,
      texture) before adding new ones, per workflow step 4.
- [x] **Wire `rack.py`** once the mapping table is settled — tempo, harmony,
      `build_groups()`.
- [x] **Tests.** Follow the existing project test convention (see
      `tests/pyoscillate/projects/lofi/`) for the new project.

## Log

- 2026-09-27: reference track analyzed (tempo/key/timbre/bass specs above);
  todo created.
- 2026-09-27: implemented as `lofi/slowed_reverb`, next to the existing
  lofi rack moved to `lofi/boom_bap` (both now subdirectories of
  `src/pyoscillate/projects/lofi/`). Grounded via the music-theory
  (E Phrygian modal centre, i-♭II vamp) and pyo-music (per-patch reverb,
  not a rack-level bus - the rack has none) skills; see
  `src/pyoscillate/projects/lofi/slowed_reverb/README.md` for the full
  mapping. New patch: `tonal/bass/hover.py`'s `BassHover`, plus a
  `voice_output()` post-processing hook added to `tonal/bass/base.py`'s
  shared `Bass` (same pattern as `Kick`/`Groove`'s own hook) so a bass style
  can add its own effects chain. The pad and texture layers reuse
  `tonal/drone`'s `SoundscapeWash` and `texture/noise`'s `NoiseDust`
  unmodified, re-tuned dark via constructor overrides. Deliberately left out
  a drums/comping layer - see the README's "What this rack does not
  attempt" for why. Tests: `tests/pyoscillate/patches/tonal/bass/test_hover.py`
  (a real gain-staging bug this surfaced - a clipping loudest corner from the
  continuous reverb tail - is recorded there, not repeated here).
