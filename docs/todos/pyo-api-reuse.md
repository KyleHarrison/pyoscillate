# TODO: reuse and feature additions from the pyo API

Source: a cross-reference of every file under
`.claude/skills/pyo-music/references/pyo-api/` against `src/` on 2026-10-04
(branch `feature/master-rack`). It finds (A) code we hand-rolled that a pyo
object already does and (B) pyo objects we don't use that would add a feature
or fit an existing slot. It complements `pyo-examples.md`, which maps the
official examples onto patch families.

## How to use this file

- **Verification status.** The survey read the API reference snapshots and
  `src/`. Nothing was run in pyo. Each item marked "check first" depends on
  pyo behaviour the reference doesn't state (sign conventions, ranges,
  threading). Prove it with a short offline render before committing to it.
- Still reason musical → sonic → synthesis → pyo (`AGENTS.md`, foundational
  principle). An unused object is a candidate mechanism, not a spec.
- **Constraints that decide adoption** (from `src/pyoscillate/AGENTS.md` and
  `patches/AGENTS.md`):
  - Every node is a named, annotated `self.<name>`. No anonymous nested
    constructors. Nodes that live only in a list go through `self.retain`.
  - No module-level functions or constants in `src/pyoscillate/`.
  - Python on the audio thread is a cost (`Clock` is a `Pattern`, and
    `start_server` sets `sys.setswitchinterval(0.0005)` for it). Prefer pure-C
    objects over new `TrigFunc`/`Pattern` callbacks. Never pass `function=` to
    an analysis object.
  - Controls are cheap, idempotent attribute writes. Use `self.live(Cls.param)`
    for glided values. Init-only constructor arguments force `rebuild=True`.
  - Clock-locked patterns take phase from `clock.tick`. Free-running timers
    (`Metro`, `Seq`, `Beat`, `Euclide`) drift from the grid and from rebuilds.

## Decisions already made (do not reopen without new evidence)

| Area | Verdict |
|---|---|
| pyo `Scope`/`Spectrum`, `Server.gui()`, `.ctrl()` | Rejected. wxPython windows, Python on the audio thread, and they can't be embedded in Flet. `LiveAnalyser` stays. |
| `Clock` (Pattern + `Division` fan-out) | Keep. `Metro`+`Counter`, `Seq`, `Beat`, `Score` and `Events` have no Python-int `tick` that survives rebuilds or supports bar lookup for `Harmony`. |
| `Events` / `EventInstrument` / `MML` | Reject. Own timing, per-event allocation, conflicts with retained ownership. |
| `Note` (pitch maths) vs `MToF`/`FToM` | Keep `Note`. Scalar Python at build/trigger time. pyo's are audio-rate nodes. |
| `Harmony.quantise` / `Scale.snap` vs `Snap` | Keep for scalar call sites. `Snap` is only a new feature (item B21). |
| `SeededDraws` / `random.Random` vs `Choice`, `Urn` | Keep. pyo has only a global seed, and the "same seed, same melody" contract needs Python `Random`. |
| `slider cutoff` taper vs `Map`/`SLMap` | Keep. pyo has only `lin`/`log`, and the 4th-power curve is deliberate. |
| `features.py` offline analysis vs `RMS`/`Centroid`/`AttackDetector`/`ZCross` | Keep. Offline, non-causal, per-hit and level-relative. pyo's are causal, per-buffer. |
| Sidechain (`Follower2` + `Clip`), `Disperse`, clap burst table, `DCBlock` | Keep. No pyo object does the same job (`Compress`/`Gate` have no key input). |

## A. Hand-rolled code a pyo object replaces

Ordered by value. Effort: S/M/L.

| # | Where | Replace with | Effort | Check first / why it may be a poor swap |
|---|---|---|---|---|
| A1 | `patches/common.py` `frequency_shift()` + `Stage`, used by `transition/riser/riser.py`, `texture/noise/noise.py` (NoiseBarber) | `FreqShift(input, shift)` | S | Confirm `shift` accepts an audio-rate signal (Barber drives it with a `Sine`), the sign convention, and range against the Hilbert version. Render both and listen. Deletes 4 retained nodes per stage, the `Stage` dataclass and a module-level function that breaks the scope rules. |
| A2 | `rebuild=True` on params that pyo can change live: `musical/generative` (`note_period`, `note_duration`), `musical/canon` (`voice_b_interval`, `root` feed a `build()`-time value, so look closer), `musical/arp`, `tonal/lead` | `Metro.time` / `TrigEnv.dur` attribute writes | S per patch | Rebuild restarts the Metro phase and drops the voice, which violates `patches/AGENTS.md` rule 3. The survey did not verify `arp.py` and `lead.py`. Check each. |
| A3 | `musical/stab/stab.py` per-note `Delay` on the trigger plus the `whole_samples()` snap workaround | `SDelay` | S | `Delay` interpolates and splits the 1-sample trigger. `SDelay` doesn't, so the workaround goes. Check that a live delay change doesn't drop a trigger. |
| A4 | `texture/noise/noise.py` crackle: `RandDur` + `Port(1/motion)` + `Change` + `click_min/max` | `Cloud(density=...)` into the existing `TrigEnv` click | S | `Cloud` gaps are Poisson-like (can cluster) where `RandDur` was uniformly bounded. More vinyl-like, less even. Pure C. |
| A5 | `tonal/bass/funk/funk.py` `note_gate` (`TrigEnv` + `LinTable`) + per-note `TrigFunc(..., note_off)` | `Adsr(dur=...)`, as `tonal/bass/fm/fm.py` already does | S-M | Removes a Python callback on the audio thread. `dur` includes release. Check "new note restarts, old release never lands on the next". Two `Adsr`s (amp, filter) both need `dur`. |
| A6 | `common.Echo.add_echo`, `tonal/lead/fm.py` tempo-synced `Delay` with a live-changed time (`SigTo` glide today) | `SmoothDelay` | S | Artefact-free time sweeps and tempo changes. About 2x reader CPU. Loses tape-warp pitch glide if that was wanted. `maxdelay` stays init-only. |
| A7 | `patches/base.py` output stage: `Compress` + hard `Clip` | `Tanh` soft limiter instead of `Clip` | S | Global tone change on every patch (compresses moderate levels). Needs an A/B listen across the rack. |
| A8 | Per-control hand-written LFO/sine: `Sine` LFOs in `noise.py`, `keys.py`, `wash.py`, `sub_swell.py`, `base.py` `tempo_sine` | `FastSine(quality=0)` | S | Pure CPU saving. Control-rate LFOs only, not audio rate. |
| A9 | `common.decay_points()` and `clap.py` polyline envelopes | `LogTable` / `ExpTable` | M | Weak. `LogTable` can't hold 0, and tables must start and end at 0. `RING_CURVE` guarantees an exact -40 dB tail that `ExpTable` doesn't. Only worth doing for the decay segment. |
| A10 | `analysis/live.py` and `patches/base.py` `_retired` keep-alive lists | `Clean_objects` | S | **Do not swap.** It deletes from a timer thread, which is the SIGSEGV that `patches/AGENTS.md` warns about. Noted so nobody tries. |
| A11 | `patches/sweep.py`: private `LFO` + 50 ms `Pattern` per sweep | A `Clock`-derived triangle (`(tick % cycle) / cycle`) from one shared `Division`, as `Evolution` does | M | N sweeps means N Python callbacks at 20 Hz on the audio thread, and the LFO phase isn't clock-locked or rebuild-stable. Where a param has a `live()` `SigTo`, `Scale(lfo, ...)` into it removes the callback entirely (partial coverage). |
| A12 | Hard-wired `Freeverb` in `stab.py`, `pluck.py` (bypasses the `Reverb` mixin); hard-wired `Chorus` in `stab.py`, `strings.py`, `drone/wash.py` | Existing `Reverb` mixin; a new shared chorus mixin (B6) | S | Consistency and fewer duplicate param definitions. |

## B. Unused pyo objects worth adding

### Effects and spectral (B1-B9)

New mixins follow the `Comb`/`Disperse`/`Flood` shape: an amount `Param`
defaulting to 0, `sweep=True`, and `add_x(source)` returning the signal.

| # | Object | Use and attach point | Effort | Risk |
|---|---|---|---|---|
| B1 | `FreqShift` | New `Shift` mixin ("Detune/Inharmonic") for pads, strings and drones. Same object as A1. | S | Large shifts sound metallic. Low CPU. |
| B2 | `Harmonizer` | "Shimmer/Octave" mixin: pitch-shifted feed into `Reverb`, or a detune/widen thickener for pads and strings (`psyambient`). | M | Window latency, comb/warble on transients and big shifts, feedback buildup, highest CPU here. `winsize` max 1 s. Keep it off drums. It shifts by ratio, so it can't follow chords. |
| B3 | `Degrade` | `Crush` mixin: "Grit" (bitdepth), "Dust" (`srscale`) for `lofi` and drums. | S | Stepping bitdepth zippers, so wrap in `live()`. |
| B4 | `Mirror` / `Wrap` | `Fold` mixin (wavefold) beside `Disto` on lead and kick. | S | Aliasing at high gain and level jumps. Follow with `Clip`/`Tone`. |
| B5 | `PV*` spectral set: `PVBuffer` (freeze), `PVBufLoops` (blur), `PVTranspose` (shimmer), `PVFreqMod`/`PVAmpMod` (warble/tremor), `PVGate` (erode), `PVVerb` | Spectral FX mixins for pads, drones and textures (`ContinuousVoice`: `psyambient`, `slowed_reverb`, `wash`). Bracket each chain with `PVAnal`/`PVSynth`. | S-M each | Latency and smear at size 1024. CPU doubles for stereo. `size`/`overlaps` are init-only, so make them `ClassVar`s. Every PV node must be an annotated `self` attribute (`_graph_objects` already handles `PyoPVObject`). Not for kicks or bass. |
| B6 | `Chorus` + `Phaser` + `Allpass2` | Shared `Ensemble` mixin (don't name it `Chorus`), replacing three hand-wired copies (A12). Phaser sibling could extend `noise.py`. | M | `Phaser.num` is init-only. Mono in gives stereo out, so mind `.mix(2)`. |
| B7 | `WGVerb` / `STRev` / `CvlVerb` | Reverb-algorithm dropdown on `common.Reverb` (`rebuild=True`), size/damp macros. `CvlVerb` as a single bus send only. | M | Rebuild on switch. `CvlVerb` is CPU-heavy, and its minimum partition (1024) equals the current buffer. |
| B8 | `AllpassWG` | Alternative `Comb` style for bell-like resonance. | S | `minfreq` init-only. Can ring and clip. |
| B9 | `EQ` | "Tilt/Warmth" tone mixin, or on the master bus (C1). | M | Keep boosts under the output ceiling. |

### Filters, oscillators and tables (B10-B22)

| # | Object | Use and attach point | Effort | Risk |
|---|---|---|---|---|
| B10 | `SVF` / `SVF2` | "Filter shape" Param (LP→BP→HP morph) on leads, pads, drones. Most patches fix `Biquad(type=0)` at build time. | S | `freq` limited to sr/6. Slightly more CPU than `Biquad`. |
| B11 | `ChebyTable` / `AtanTable` + `Lookup` | Tunable waveshaper ("Grit" per harmonic) where `Disto` has one fixed curve (`kick`, `snare`, `hat/groove`, `lead`). | M | `Lookup` needs input in -1..1. Smooth table rewrites. No oversampling (see B12). |
| B12 | `Resample` + `beginResamplingBlock`/`endResamplingBlock` | Oversample `Disto` shapers to cut aliasing. | M | CPU multiplies by the factor inside the block. Blocks follow creation order. Test across rebuilds. |
| B13 | `TableMorph` over `HarmTable`s | Live "Morph" timbre Param on bass, drone and stab oscillators (`bass/base.py`, `sub_swell`, `sub_chaos`, `filter`, `stab`). | M | Recomputes an 8192-point table per buffer while moving. Smooth with `live()`. Source list fixed at build. |
| B14 | `OscBank` | Placeholder `tonal/bass/reese`, thick lead, and an alternative to the `SuperSaw` stacks in `strings.py`. | M (reese), S (strings) | Moderate CPU at `num=24`. Map "Spread"→`spread`, "Movement"→`frnda`/`arnda`. |
| B15 | `PadSynthTable` | `tonal/pad` and a richer `drone/filter` source. | M | 262144-point table, slow to build (build-time only). Pitch fixed to `basefreq`. |
| B16 | `PartialTable` | Bell/hat/cymbal alternative to FM operators, with partial ratios as tunable data. | S | Static 65536-point table, so partials don't follow Brightness. |
| B17 | `SumOsc`, `Blit`, `SineLoop`, `ChenLee` | New drone/lead/bass styles. `SumOsc.index` gives a low-aliasing Brightness macro. `ChenLee` is a third chaos source (could replace the fixed tape wobble in `keys.py`). | S-M | Each is a new topology (a style subclass, not a Param). Pair `SumOsc`/`Blit` with `ButHP` for DC. |
| B18 | `Cloud` (poly) | New `texture/` styles (rain, crackle, granular-ish) with a density Param. Same object as A4. | S | Not clock-locked, fine for textures. `poly` init-only. |
| B19 | `TrigBurst` | `Roll`/`Ratchet` mixin between `self.trigger` and `envelope()` for hat rolls, flams and snare rolls. | M | Free-running timer, though sub-step fills are short. Check `TrigEnv`'s trigger threshold (the stab comment says it fires only on 1.0). |
| B20 | `Randi` / `Randh` | Cheap slow-wander macro for detune, cutoff and pan in drones. | S | Unseeded (global seed only). |
| B21 | `Snap` + `SampHold`/`TrackHold` | Chaos- or LFO-driven pitch that always stays in the rack's key (`wash.py`, `sub_chaos.py`). | M | Re-push `choice` on key/scale change. Short glide to avoid clicks. Not for the existing micro-pitch wander. |
| B22 | `XnoiseMidi` | Walk/Poisson melodic character in `musical/generative`. | M | Loses the deterministic `seed`. Only if that's accepted. |

### Stereo, space and the master bus (C1-C4)

| # | Object | Use and attach point | Effort | Risk |
|---|---|---|---|---|
| C1 | Master bus: `Mixer`/`Mix`, `Compress`, shared reverb send, optional `BandSplit`/`FourBand` | Today each patch `.out()`s directly, runs its own `Compress`+`Clip`, and 9 patches run their own `Freeverb`. Master control is only `server.setAmp`. A `Rack`-owned `MasterBus` (in `pyoscillate/`, passed through `BuildContext`) gives one glue compressor and limiter, shared sends, click-free per-patch mute/level, and a tap for `LiveAnalyser.attach_sum`. | M-L | Largest CPU win and largest redesign. `Patch.start()` registers with the bus instead of `.out()`. `stop(wait=...)` and `_retired` must also remove the input. `Mixer.addInput`/`delInput` while running need care. |
| C2 | `SPan` / per-channel gains | `pan` Param on `Patch` (`sweep=True`) at `base.py` output. Every dry drum is dead-centre today. | S-M | Voices with `Freeverb`/`Chorus` are already stereo, and `Pan` on 2 streams yields 4. Pan a mono sum, or use equal-power gains on `[0]`/`[1]`. Retain nodes in `_output_resources`. |
| C3 | `HRTF` (preferred) / `Binaural` | "Position" azimuth/elevation Param for psyambient and forest. Opt-in headphone mode. | M | Wrong on speakers. Feed azimuth through `SigTo`. `Binaural` costs more than `HRTF`. |
| C4 | `PVCross` / `PVMorph` | Cross-synthesis between two patches (pad shaped by hat). A rack-level link like `Sidechain`. | L | Two sources in one graph, so lifecycle coordination. |

### Metering, analysis and recording (D1-D5)

| # | Object | Use and attach point | Effort | Risk |
|---|---|---|---|---|
| D1 | `PeakAmp` / `RMS` with `.get()` | Per-patch level bar in `PatchPanel` and the minimal app, plus clip warnings. Poll on the existing `refresh_analysis` tick. | S | No `function=`. One extra node per playing patch, retained and stopped in `stop()`. |
| D2 | `Centroid` / `Yin` | Live brightness and pitch readouts next to the spectrum. `Yin` offline in `Features` to check pitched patches sit on `Note` values. | S live, M offline | `Yin` `minfreq` defaults to 40, so use 20 and `winsize=2048` for sub-bass. `Centroid` only for continuous signals. |
| D3 | `Record` | "Record patch / rack" button. Only offline `render.py` writes files today. | S | Needs a file path (the app has a `catalog_dir`). Start/stop UI belongs in `flet/`. |
| D4 | `AttackDetector` | Hit flash on the kick meter, or a trigger from a patch's output. | M | Per-source threshold tuning, false onsets on noise. |
| D5 | `ControlRec` / `ControlRead` | Recorded slider automation generalising `Sweep`. | L | Replay still needs a `Pattern`, so it inherits the audio-thread cost. Presets cover most of it. |

### External control (E1-E4)

| # | Object | Use and attach point | Effort | Risk |
|---|---|---|---|---|
| E1 | `MidiListener` + `CtlScan2` (learn) | `MidiMap` class mapping (channel, cc) to a `Param` (`param.write`) or a `GroupControl` (`GroupRuntime.apply(control, cc/127)`, already 0-1). Store the map in the preset JSON. | M (S hardcoded) | Listener runs on its own thread. Coalesce high-rate CCs and marshal repaints onto the UI loop. The device can't be shared with the audio server (`deactivateMidi()`). `start_server` doesn't configure MIDI. Don't use `Midictl` (audio-rate stream). |
| E2 | `OscListener` (+ `OscDataSend` out) | External control (TouchOSC, DAW) at `/<patch.name>/<param.name>`, `/bpm`, `/key`, `/group/<n>/<control>`. Publish bar, chord and sweep position from a bar-length `Division`. | M | Open port, same threading as E1. External only: the UI→engine path stays an in-process `Param.write`. |
| E3 | `Programin` / `Notein` as control | Program change switches style variants. Pitch class sets `Harmony.key`. | S | Not a played voice: that conflicts with `GatedVoice.finish()` needing `schedule()`. |
| E4 | `MidiDispatcher` (MIDI out) | Mirror `GatedVoice.next_step` hits to hardware/DAW. | M | Note-offs need a timer. Python send in the tick adds jitter. Low priority. |

### Sample family (F1-F3)

| # | Object | Use and attach point | Effort | Risk |
|---|---|---|---|---|
| F1 | `SndTable` + `TableRead`/`Pointer2`/`Looper`/`Granulator`/`Particle2` | Fill `patches/sample/{playback,grains,breakbeat}`. | L | Needs a file loader, catalog and asset-path Param type. Blocking load at build. Granular voices are CPU-heavy. |
| F2 | `SfMarkerLooper` / `SfMarkerShuffler` | `sample/breakbeat`. `mark` is an integer slice index, which equals a phrase step `value`. | M | Needs AIFF files with marker chunks. `mark`/`speed` read once per buffer. |
| F3 | `SfPlayer` | Long beds in `sample/playback` as a `ContinuousVoice`. | S-M | May stream from disk in the audio callback (unconfirmed). Keep clips small, or use `SndTable` + `Looper` for one-shots. |

### Ideas

- `Euclide` / `Beat` patterns as `Phrase` entries under `theory/phrase`. Pure
  Python data, clock-locked, no audio-thread cost (the pyo objects free-run).
- `TrigXnoise` distributions (walker, cauchy, ...) ported as `Walks` styles
  rather than adopted as objects.

## Suggested order

1. **A1 `FreqShift`** — render both versions of the riser and Barber, then
   delete `frequency_shift`/`Stage`. Also unblocks B1.
2. **A2 live-time params** — a usability fix, not just refactoring.
3. **D1 level meters** and **C2 pan** — small, visible wins.
4. **B2 `Harmonizer`** shimmer and **B3/B4** `Degrade`/`Mirror` — small fx
   mixins, one per day.
5. **C1 master bus** — plan it as its own design doc before any code. It
   touches `Patch.start()`/`stop()`, `BuildContext` and `LiveAnalyser`.
6. **E1 MIDI CC map** — after the bus, so levels and sends are mappable.
7. **F-series samples** — needs an asset pipeline decision first.

## Open questions

- A1: does `FreqShift` accept an audio-rate `shift`, and is its sign
  convention the same as the Hilbert version?
- A5: does `Adsr(dur=)` keep "a new note restarts, its release never lands on
  the next"?
- C1: is the saving from one shared reverb and limiter worth the lifecycle
  change? Measure per-patch `Freeverb`+`Compress` CPU first (9 patches run a
  `Freeverb` today).
- F3: does `SfPlayer` do disk I/O inside the audio callback?
