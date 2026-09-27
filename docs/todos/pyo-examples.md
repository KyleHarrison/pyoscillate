# TODO: patch candidates from the official pyo examples

Source: a pass over <https://belangeo.github.io/pyo/examples/index.html>
(pyo 1.0.6) on 2026-09-24. This lists the examples that map onto patch
families in `src/pyoscillate/patches/`. Families that have no builder yet are
listed first.

## How to use this file

- An example is a **mechanism reference**, not a patch spec. Still reason
  musical → sonic → synthesis → pyo through the skill chain, and fill in the
  family's `AGENTS.md` before the first build (see `patches/AGENTS.md`,
  placeholders).
- Many examples use `SfPlayer("…drumloop.wav")` only as a demo input. The
  effect is independent of the source, so feed it one of our synth voices.
- Examples set values with `.ctrl()` GUIs and module globals. When porting, map
  them to `SliderSpec` + `Patch.controls`, name every intermediate, and list
  each one in `resources`.

## Tier 1: fills a family that has no builder yet (synth-only, no soundfile)

| Family | Example(s) | What to take from it |
|---|---|---|
| `pitched_percussion/bell` | [x06/03 complex resonator](https://belangeo.github.io/pyo/examples/x06-filters/03-complex-resonator.html), [x03/03 FM](https://belangeo.github.io/pyo/examples/x03-generators/03-fm-generators.html), [x10/01 envelopes](https://belangeo.github.io/pyo/examples/x10-tables/01-envelopes.html) | Two routes. (a) **Modal/chime**: a `Metro` impulse excites a `ComplexRes` bank at inharmonic frequencies. Decay is a live control, and `Pattern` retunes the partials. The bell doc doesn't mention this route yet; add it as a design alternative. (b) **Chowning FM**: `FM` with a non-integer `ratio` and an index envelope that falls over the note. This matches the doc's "FM network". |
| `tonal/bass/fm` | x03/03 FM, x10/01 envelopes | `FM` with an integer `ratio`. Its index follows a break-point table (`LinTable` 20 → 0) read by `TableRead`: the doc's "bark then settle". `CrossFM` (`ind1`/`ind2`) is a second, grittier profile. |
| `tonal/keys` | x10/01 envelopes | FM with three break-point envelopes (amp `CosTable`, ratio `ExpTable`, index `LinTable`). Reader freq = `1/dur`, so the same shape scales to any note length. That fits an electric-piano "tine": index envelope = bark, and velocity can scale the index. |
| `tonal/lead` | [x03/01 complex oscs](https://belangeo.github.io/pyo/examples/x03-generators/01-complex-oscs.html), [x05/03 exponential ramp](https://belangeo.github.io/pyo/examples/x05-envelopes/03-exponential-ramp.html), [x03/06 random generators](https://belangeo.github.io/pyo/examples/x03-generators/06-random-generators.html) | Brightness from one oscillator parameter: `Blit.harms`, `RCOsc.sharp` or `SineLoop.feedback`. `Selector` morphs between them as a "character" control. `Port(risetime≠falltime)` gives asymmetric portamento (fast rise, slow fall). `Randi` in the ±0.7% range gives natural pitch drift. |
| `tonal/pluck` | x06/03 complex resonator, x03/01 complex oscs | Impulse → resonator is the doc's "short transient into a resonant network". A second profile: `Blit` with a `harms` envelope that decays fast is the "brightness contour". |
| `texture/noise` | [x03/04 noise generators](https://belangeo.github.io/pyo/examples/x03-generators/04-noise-generators.html), [x06/04 phasing](https://belangeo.github.io/pyo/examples/x06-filters/04-phasing.html), [x06/07 Hilbert](https://belangeo.github.io/pyo/examples/x06-filters/07-hilbert-transform.html) | A `Selector` over `Noise`/`PinkNoise`/`BrownNoise` gives one "colour" slider. `Phaser(num=20)` on pink noise, with separate slow LFOs on freq/spread/q per channel, gives surf/wind movement. The Hilbert frequency shift gives a slow barber-pole motion. None of these need a soundfile. |
| `transition/riser` | x06/07 Hilbert, [x05/05 break-point functions](https://belangeo.github.io/pyo/examples/x05-envelopes/05-breakpoints-functions.html), x05/02–03 ramps | Hilbert + quadrature `Sine` frequency shift (single sideband) = an endless barber-pole rise with no audible top. Sweep the shift amount over bars with `Linseg`/`Expseg` timed from the tempo. |
| `tonal/strings` | [x07/05 hand-made chorus](https://belangeo.github.io/pyo/examples/x07-effects/05-hand-made-chorus.html), x03/01 (`SuperSaw`) | 8 `Delay` lines modulated by `Sine` LFOs at unrelated rates (0.25–1.9 Hz, 9–18 ms centre, 1–2.3 ms depth). Odd lines go left and even lines right. This is the "ensemble chorus" stage the doc asks for, and it gives more control than the `Chorus` object. |
| `tonal/pad` | [x10/07 moving points](https://belangeo.github.io/pyo/examples/x10-tables/07-moving-points.html), x03/01, x06/04 | A `Pattern` rewrites a small `LinTable` (256 pts) from two slow LFOs every 50 ms. `Osc` reads it as an amplitude/brightness shape that keeps changing: a "breathing" pad. Keep the table small; rewriting large tables glitches. |
| `tonal/bass/reese` | x03/01 (`SuperSaw.detune`), x07/05 | Weaker fit. SuperSaw detune is the beating control. The example only shows the object, not a bassline. |
| `tonal/bass/acid` | x05/03 exponential ramp, [x07/03 fuzz](https://belangeo.github.io/pyo/examples/x07-effects/03-fuzz-disto.html) | Only parts: `Port` for slide, and the asymmetric transfer-function fuzz for the overdrive stage. No per-note filter-envelope example. Use the Devil Fish manual (`sources.md`) for that. |

## Tier 2: new profiles or topologies for existing families

| Family | Example | Idea |
|---|---|---|
| `tonal/drone` (or `texture/`) | [x15/01 wave terrain](https://belangeo.github.io/pyo/examples/x15-matrix/01-wave-terrain-synthesis.html), [x15/02 matrix record](https://belangeo.github.io/pyo/examples/x15-matrix/02-matrix-record.html) | `NewMatrix` 512×512 sine terrain, scanned by `MatrixPointer` with six detuned `Sine` x-scans (50–151 Hz) and a random-depth y-scan. The x-scan rates set a pitch centre, so it's a drone. Scanning at sub-audio rates would make it texture. x15/02 records live FM into the terrain. |
| `musical/generative` | x03/06 random generators, [x22/07 managing scales](https://belangeo.github.io/pyo/examples/x22-events/07-managing-scales.html), [x22/09 embedding generators](https://belangeo.github.io/pyo/examples/x22-events/09-embedding-generators.html) | `Choice` with a list `freq` = two unsynchronised pitch streams. `EventScale` + `EventDrunk(maxStep)` gives a random walk kept inside a scale, and the scale is regenerated at the end of each phrase (`atend`). Embedding generators build phrases → progressions. `Events` is its own scheduler, so port the ideas into our `Sequencer`; don't adopt `Events` wholesale. |
| `texture/atmosphere` | [x06/06 vocoder](https://belangeo.github.io/pyo/examples/x06-filters/06-vocoder.html) | `Vocoder(stages=32)` with freq/spread/q/slope each on its own slow LFO (0.06–0.11 Hz). Use a synth voice as the spectral source instead of the speech file. |
| drums (snare/tom/clap) | [x08/03 gated verb](https://belangeo.github.io/pyo/examples/x08-dynamics/03-gated-verb.html) | `Gate(outputAmp=True)` on the dry hit multiplies a big `Freeverb` → `Compress`: the 80s gated snare. The example uses a loop, but a synthesised snare works the same way. |
| bass / lead drive stages | x07/03 fuzz, [x10/08 table lookup](https://belangeo.github.io/pyo/examples/x10-tables/08-table-lookup.html) | Asymmetric fuzz: two `ExpTable` halves summed into one transfer table, read through `Lookup` after a `ButBP` + gain boost, then `ButLP`. `AtanTable(slope)` + `Lookup` is a softer, symmetric alternative. Candidate shared helper in `common.py`. |

## Tier 3: needs sample infrastructure first (all `sample/` placeholders)

| Family | Example | Idea |
|---|---|---|
| `sample/playback` | [x10/03 looper](https://belangeo.github.io/pyo/examples/x10-tables/03-looping.html), x04/03 read from RAM | `Looper` over a `SndTable`: pitch, start/dur, xfade %, mode (fwd/back/ping-pong), `autosmooth`. Its `['trig']` and `['time']` outputs can drive other patches. |
| `sample/grains` | [x10/04 granulation](https://belangeo.github.io/pyo/examples/x10-tables/04-granulation.html), [x10/05 micro-montage](https://belangeo.github.io/pyo/examples/x10-tables/05-micro-montage.html) | `Particle2` + `WinTable` (Tukey window), 128 grains/s, 0.2 s grains. Position = slow `Sine` × small `Noise` jitter, which stops the phasing you get when grains overlap. |
| `sample/breakbeat` | [x10/06 table stutter](https://belangeo.github.io/pyo/examples/x10-tables/06-table-stutter.html) | `Pointer` + `Linseg` + `Fader` retriggered by `Pattern`: stutter/retrigger with click-free fades. It isn't slice resequencing, but it covers the playback and fade mechanics. |

All three need a decision on how a rack loads and owns a `SndTable`: where files live and which parameters force a rebuild. Make that decision before any of these.

## Rack-level (not patch families)

- [x08/02 ducking](https://belangeo.github.io/pyo/examples/x08-dynamics/02-ducking.html) and [x08/04 auto-wah](https://belangeo.github.io/pyo/examples/x08-dynamics/04-rms-tracing.html): `Follower` → `Scale` → a parameter. This is the "one voice's amplitude modulates another" link: kick ducks the pad, and the drum envelope opens the bass filter. It belongs in `linked-rack-modulation.md`, not in a patch.
- Effects that could become a shared send/bus: x07/01 flanger, x07/02 Schroeder reverb (4 prime-spaced combs → 2 allpasses), x07/04 ping-pong delay, x07/06 harmonizer, and x14/04 spectral delay (`FFT` → per-band `Delay` → `IFFT`).
- x14/02–03 FFT cross-synthesis and morphing: two of our voices morphing into each other. This is interesting, but it needs two voices routed into one processor, so it depends on the rack-linking design.

## Skipped

x01, x02 (basics/GUI), x04/01–02 and 04–06 (disk playback and recording), x09 (callbacks: we already use `Pattern`/`TrigFunc`), x16/x17 (MIDI/OSC), x19 (multirate; revisit only if drive stages alias), x20 (multicore), x21 (utilities), x23 (`Expr`). One exception in x23: 04's phase-aligned formant (PAF) generator is a candidate "vocal/formant" lead profile if we want one.

## Tasks

Work the phases in order; tasks inside a phase can go in any order unless a
dependency is noted. The tables above hold the detail for each example. Tick a
box when the task lands and add a line to the Log.

**Done means:** the family's `AGENTS.md` is filled from sources (placeholder
status dropped), the module exposes `PARAMETERS` + `build()`, every graph
object is in `voice`/`sequencer`/`resources`, controls update live where the
topology allows, the patch is registered in its family `__init__.py`, 

### Phase 1: `texture/noise`

- [x] Fill `texture/noise/AGENTS.md` from sources; drop placeholder status
- [x] x03/04 noise generators → first noise patch with a white/pink/brown "colour" control (`Selector`)
- [x] x06/04 phasing → phaser movement profile (`Phaser(num=20)`, independent slow LFOs per channel)
- [x] x06/07 Hilbert → barber-pole frequency-shift profile

### Phase 2: `transition/riser`

- [x] Fill `transition/riser/AGENTS.md`; drop placeholder status
- [x] x06/07 Hilbert → endless-rise source (single-sideband shift)
- [x] x05/05 break-point functions → rise shape over a duration set in bars from the tempo (`Linseg`/`Expseg`)
- [x] x05/02–03 linear/exponential ramps → pitch and level climb (`SigTo`, `Port`)

### Phase 3: FM family (shared break-point-envelope pattern)

- [x] Add the modal/resonator route to `pitched_percussion/bell/AGENTS.md` as a design alternative
- [x] x06/03 complex resonator → bell chime profile (`Metro` impulses into a `ComplexRes` bank)
- [x] x03/03 FM + x10/01 envelopes → Chowning FM bell profile (non-integer ratio, falling index)
- [x] Fill `tonal/bass/fm/AGENTS.md`; drop placeholder status
- [x] x03/03 FM + x10/01 envelopes → FM bass with index envelope ("bark then settle")
- [x] x03/03 `CrossFM` → gritty FM bass profile
- [x] Fill `tonal/keys/AGENTS.md`; drop placeholder status
- [x] x10/01 envelopes → electric-piano tine (amp/ratio/index tables, reader freq = `1/dur`, velocity scales index)

### Phase 4: shared drive stage (before lead and acid)

- [ ] x07/03 fuzz → asymmetric transfer-function drive helper in `common.py` (`ExpTable` halves + `Lookup`)
- [ ] x10/08 table lookup → soft symmetric drive option (`AtanTable(slope)` + `Lookup`)

### Phase 5: `tonal/lead` and `tonal/pluck`

- [ ] x03/01 complex oscs → lead "character" control morphing `Blit.harms` / `RCOsc.sharp` / `SineLoop.feedback`
- [ ] x05/03 exponential ramp → asymmetric portamento (`Port` rise ≠ fall)
- [ ] x03/06 random generators → subtle pitch drift (`Randi`, ±0.7%)
- [ ] Aggressive lead profile using the Phase 4 drive helper
- [ ] (Optional) x23/04 let function → phase-aligned formant "vocal" lead profile via `Expr`
- [ ] x06/03 complex resonator → pluck body (impulse into resonator)
- [ ] x03/01 complex oscs → electronic pluck profile (`Blit` with fast-decaying `harms`)

### Phase 6: `tonal/strings` and `tonal/pad`

- [ ] Fill `tonal/strings/AGENTS.md`; drop placeholder status
- [ ] x07/05 hand-made chorus → reusable 8-line ensemble chorus helper
- [ ] x03/01 `SuperSaw` → string section source feeding the ensemble chorus
- [ ] x10/07 moving points → "breathing" pad (small `LinTable` rewritten by slow LFOs via `Pattern`)
- [ ] x06/04 phasing → pad movement option

### Phase 7: remaining bass sub-families

- [ ] Fill `tonal/bass/reese/AGENTS.md`; drop placeholder status
- [ ] x03/01 `SuperSaw.detune` → Reese beating control
- [ ] x07/05 hand-made chorus → optional Reese widening (reuse Phase 6 helper)
- [ ] Fill `tonal/bass/acid/AGENTS.md` (Devil Fish manual for the filter envelope); drop placeholder status
- [ ] x05/03 exponential ramp → acid slide (`Port`)
- [ ] x07/03 fuzz → acid overdrive (reuse Phase 4 helper)

### Phase 8: new profiles for existing families

- [ ] x15/01 wave terrain → drone profile (`NewMatrix` + `MatrixPointer`)
- [ ] x15/02 matrix record → wave terrain fed by live FM
- [ ] x03/06 random generators → generative two unsynchronised pitch streams (`Choice` list `freq`)
- [ ] x22/07 managing scales → scale-bounded random walk, scale regenerated per phrase (port into our `Sequencer`)
- [ ] x22/09 embedding generators → nested phrase/progression generation (port into our `Sequencer`)
- [ ] x06/06 vocoder → atmosphere profile with a synth voice as the spectral source
- [ ] x08/03 gated verb → gated-reverb option on snare/tom/clap (`Gate(outputAmp=True)` → `Freeverb` → `Compress`)

### Phase 9: sample families

- [ ] Decide how a rack loads and owns a `SndTable` (file location, which params force a rebuild) — ask the user
- [ ] Fill `sample/playback/AGENTS.md`; drop placeholder status
- [ ] x10/03 looper → playback patch (`Looper`: pitch, start/dur, xfade, mode)
- [ ] x04/03 read from RAM → one-shot playback profile
- [ ] Fill `sample/grains/AGENTS.md`; drop placeholder status
- [ ] x10/04 granulation → grains patch (`Particle2` + `WinTable`, sine × noise position)
- [ ] x10/05 micro-montage → random-chunk table profile
- [ ] Fill `sample/breakbeat/AGENTS.md`; drop placeholder status
- [ ] x10/06 table stutter → stutter/retrigger mechanics (`Pointer` + `Linseg` + `Fader`)

### Phase 10: rack-level (depends on `linked-rack-modulation.md`)

- [ ] x08/02 ducking → hand to `linked-rack-modulation.md` task 5 (kick ducks pad/bass)
- [ ] x08/04 auto-wah → hand to `linked-rack-modulation.md` (envelope follower → filter)
- [ ] x07/01 flanger → shared effect
- [ ] x07/02 Schroeder reverb → shared effect
- [ ] x07/04 ping-pong delay → shared effect
- [ ] x07/06 harmonizer → shared effect
- [ ] x14/04 spectral delay → shared effect
- [ ] x14/02 cross-synthesis → two-voice processor
- [ ] x14/03 spectral morphing → two-voice processor

## Log

- 2026-09-24: examples surveyed and mapped; task list created.
- 2026-09-24: Phase 1 done. `texture/noise/noise.py` (styles `air`, `surf`, `barber`); `frequency_shift`, `Stage` and `SequencerGroup` added to `patches/common.py`; `windows`/`spectral_movement` added to `analysis/features.py`. Finding: pyo's `Phaser` is a pure allpass, so x06/04's output alone has a flat spectrum; `surf` sums it with the dry bed (see `test_noise.py`).
- 2026-09-25: Phase 2 done. `transition/riser/riser.py` (styles `noise`, `shift`, `pitch`) on an 8-bar phrase, Length 1–8 bars. One `Linseg` ramp raised to a live power (Surge) drives climb, filter and level, instead of `SigTo`/`Port`: `Port` is a one-pole lag (front-loaded, the wrong shape for a build) and neither restarts from zero per shot. The shift source climbs by SSB shift within the gesture, but it isn't a true endless barber-pole; that needs a shift inside a feedback delay, recorded as a design alternative in the riser `AGENTS.md`. The noise band gets 1/√centre makeup (constant-Q bandwidth grows with the centre, which clipped at Climb 4). Also fixed ruff RUF007 in `analysis/features.py`.
- 2026-09-25: Phase 3 done. `pitched_percussion/bell/bell.py` (styles `chime`, `fm`), `tonal/bass/fm/fm.py` (styles `bark`, `grit`) and `tonal/keys/keys.py`, with `decay_points` and `RING_CURVE` in `patches/common.py` as the shared break-point envelope (`TrigEnv` `dur` plays the reader-frequency-1/dur role of x10/01's `TableRead`). The bell's modal route uses church-bell partial ratios with per-partial decay, not x06/03's random frequencies; that wind-chime version is recorded as a design alternative. Keys leave out x10/01's ratio table (a moving ratio sounds like a synth sweep, not a struck tine); a second, fixed 14:1 tine pair takes its place. Findings: ratio-1 FM puts a sideband on 0 Hz, and because pyo's `FM` integrates frequency it doesn't cancel, so the FM bass and keys carry a DC offset that follows the index envelope. Both got a 20 Hz `ButHP` (`DCBlock` is too slow). The keys' tine carrier, left ringing, partly cancelled the body after a hard strike (-7 dB), so the tine pair got its own 0.3 s envelope at half level. Both findings are in the test docstrings. `ComplexRes` `decay` is a 1/e time constant (-40 dB at ~4.6× decay).
