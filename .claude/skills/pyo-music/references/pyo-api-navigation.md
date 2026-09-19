# Pyo API Navigation

Routes a **synthesis concept** (not a musical concept — see `00-navigation.md`
for that layer) to the `pyo-api/` file that documents the implementation
options for it. This file is the join between "what kind of mechanism do I
need" and "which Pyo objects exist for that."

`pyo-api/` is the authoritative, hand-maintained description of every Pyo
object this project has documented — module docstring explains the role,
each class's docstring gives its real constructor signature. **Never invent
a Pyo constructor argument or behaviour.** If a file doesn't mention it, open
the file and read it before writing code; don't guess from general Pyo
knowledge, and don't reproduce the docstrings here — read them at the source.

## How to use this

1. You should already have a synthesis-level idea, not just the user's original words — e.g. "needs continuous, non-repeating modulation" or "needs a rhythmic trigger source," not "make it organic." Getting from the musical description to that idea is `00-navigation.md`'s and `music-composition-skill-notes.md`'s job, not this file's.
2. Find the row below matching that idea. Most rows list **more than one candidate** — that's intentional. Pick based on the specific character wanted (e.g. `Rossler` vs `Lorenz` for "organic": both are non-repeating, but Rossler wanders more smoothly, Lorenz is more angular).
3. Open the actual file and read the docstrings for every candidate before choosing. The one-line hints below exist to narrow the search, not to replace reading the file.
4. If a request spans several rows (it usually does — "evolving texture" needs a generator *and* a modulator *and* maybe an effect), load each relevant file, don't just skim this table.
5. Look at `src/pyoscillate/patches/` for how these categories actually get wired together end to end (see "Worked examples" below) before assuming an architecture from theory alone.

## Core signal chain (`pyo-api/core/`)

Every patch is: timing → triggered/continuous control → generator → filter/effect → dynamics → output. This is the backbone; start here for almost anything.

Every file below is named after (and documents **only**) one real `pyo/lib/*.py` source module — e.g. `Metro` lives in `core/triggers.py` because it's defined in `pyo/lib/triggers.py`, not in some generic "core" module. Each file's header docstring states its source module explicitly; trust that over the class's apparent category.

| Synthesis need | File | Source module | What's inside (read the file for real params) |
|---|---|---|---|
| A raw sound source — pitched oscillator or noise (not table-driven) | [`core/generators.py`](./pyo-api/core/generators.py) | `pyo/lib/generators.py` | `Sine`, `FastSine`, `SineLoop`, `Phasor`, `Input`, `Noise`, `PinkNoise`, `BrownNoise`, `FM`, `CrossFM`, `Blit`, `Rossler`, `Lorenz`, `ChenLee`, `LFO`, `SumOsc`, `SuperSaw`, `RCOsc` — periodic oscillators, noise sources, chaotic attractors (`Rossler`/`Lorenz`/`ChenLee`), and ready-made LFOs all live in this one module |
| A wavetable-driven generator, granular player, or table recorder | [`core/tableprocess.py`](./pyo-api/core/tableprocess.py) | `pyo/lib/tableprocess.py` | `Osc`, `OscLoop`, `OscTrig`, `OscBank`, `TableRead`, `Pulsar`, `Pointer`, `Pointer2`, `TableIndex`, `Lookup`, `TableRec`, `TableWrite`, `TableMorph`, `Granulator`, `Granule`, `Looper`, `Particle`, `Particle2`, `TableScan`, ... |
| A precomputed shape/waveform/curve for a table-driven generator or envelope to read | [`core/tables.py`](./pyo-api/core/tables.py) | `pyo/lib/tables.py` | `HarmTable`, `SawTable`, `SquareTable`, `HannTable`, `LinTable`, `CosTable`, `CurveTable`, `ExpTable`, `SndTable`, `NewTable`, `PadSynthTable`, ... — data buffers, not audio signals themselves |
| Discrete rhythmic pulses, or something that reacts fresh each time a trigger fires | [`core/triggers.py`](./pyo-api/core/triggers.py) | `pyo/lib/triggers.py` | Generators: `Metro` (isochronous), `Beat` (weighted/algorithmic), `Trig` (one-shot), `Seq`, `Cloud`, `Euclide`, `TrigBurst`. Reactive: `TrigEnv`, `TrigRand`, `TrigChoice`, `TrigFunc`, `TrigLinseg`, `TrigExpseg`, `TrigXnoise(Midi)`, `Counter`, `Select`, `Change`, `Thresh`, `Timer`, `Iter`, `Count`, `NextTrig`, `TrigVal` — generation and reaction both live in this one module |
| A control-signal shape driven by note-on/off or a line segment list | [`core/controls.py`](./pyo-api/core/controls.py) | `pyo/lib/controls.py` | `Fader`, `Adsr`, `Linseg`, `Expseg`, `SigTo` |
| Reshaping an existing signal's spectrum — resonant/band filters, EQ, IR-based filters | [`core/filters.py`](./pyo-api/core/filters.py) | `pyo/lib/filters.py` | `Biquad(x/a)`, `EQ`, `Tone`/`Atone`, `Port`, `BandSplit`/`FourBand`/`MultiBand`, `Allpass(2)`, `Phaser`, `Vocoder`, `SVF(2)`, `Reson`/`Resonx`, `ButLP`/`ButHP`/`ButBP`/`ButBR`, `MoogLP`, `ComplexRes`, `Hilbert`, `IRWinSinc`/`IRAverage`/`IRPulse`/`IRFM`, ... |
| Distortion, delay, reverb, chorus, pitch/frequency shift | [`core/effects.py`](./pyo-api/core/effects.py) | `pyo/lib/effects.py` | `Disto`, `Delay`/`SDelay`/`Delay1`/`SmoothDelay`, `Waveguide`/`AllpassWG`, `Freeverb`/`STRev`/`WGVerb`, `Convolve`, `Chorus`, `Harmonizer`, `FreqShift` |
| Managing loudness/level range rather than spectrum (limiting, gating, clipping, folding) | [`core/dynamics.py`](./pyo-api/core/dynamics.py) | `pyo/lib/dynamics.py` | `Compress`, `Gate`, `Clip`, `Mirror`, `Degrade`, `Balance`, `Expand`, `Min`, `Max` |
| Signal mixing, value-holding/smoothing (`Sig`, portamento), power/wrap/compare math | [`core/signal_utils.py`](./pyo-api/core/signal_utils.py) | `pyo/lib/_core.py` | `Mix`, `Sig`, `VarPort`, `Pow`, `Wrap`, `Compare`, `InputFader` — these ship in pyo's `_core` module, not a topical one; `Wrap` in particular is easy to misattribute to dynamics/filters |
| Booting/configuring the audio engine | [`core/server.py`](./pyo-api/core/server.py) | `pyo/lib/server.py` | `Server` |
| Sending a finished signal to speakers | [`core/output.py`](./pyo-api/core/output.py) | n/a (methods on `PyoObject`) | `.out()` / `.play()` / `.stop()` — methods every `PyoObject` inherits, not a separate class |

**Continuous vs. trig-reactive is the single most important distinction to get right** when a description implies "movement" or "change." Both live in `triggers.py`/`generators.py` and plug into the same parameter slots on a generator or filter — the difference is purely in what drives them: gated by a discrete event, or ongoing and ungated (an `LFO`/`Rossler`/`Lorenz` from `generators.py`).

## Beyond the core chain — not yet used in this project's patches, still fully documented

These are real, available categories; "not used yet" means no existing patch happens to need them, not that they're unavailable or unreliable. As above, each file documents exactly one `pyo/lib/*.py` source module.

| Synthesis need | File | Source module | What's inside |
|---|---|---|---|
| Measuring an existing signal instead of generating one — envelope following, pitch tracking, brightness/onset detection, scope/spectrum display | [`pyo-api/analysis/analysis.py`](./pyo-api/analysis/analysis.py) | `pyo/lib/analysis.py` | `Follower`/`Follower2`, `ZCross`, `Yin`, `Centroid`, `AttackDetector`, `Spectrum`, `Scope`, `PeakAmp`, `RMS` |
| Per-sample math as an audio-rate object | [`pyo-api/analysis/arithmetic.py`](./pyo-api/analysis/arithmetic.py) | `pyo/lib/arithmetic.py` | `Sin`/`Cos`/`Tan`/`Atan2`, `Abs`, `Sqrt`, `Log`/`Log2`/`Log10`, `Floor`/`Ceil`/`Round`, `Tanh`, `Exp`, `Div`, `Sub` |
| A small text-based DSP expression language | [`pyo-api/analysis/expression.py`](./pyo-api/analysis/expression.py) | `pyo/lib/expression.py` | `Expr` |
| Unit conversion, freezing a continuous signal into stepped values, recording to disk, MIDI/dB/Hz conversion | [`pyo-api/analysis/utils.py`](./pyo-api/analysis/utils.py) | `pyo/lib/utils.py` | `Scale`, `SampHold`, `Interp`, `Snap`, `Record`, `ControlRec`/`ControlRead`, `DBToA`/`AToDB`, `MToF`/`FToM`, `MToT`, `CentsToTranspo`/`TranspoToCents`, `Between`, `TrackHold`, `Resample`, `Denorm` |
| Free-running random values as an alternative flavor of continuous modulation (stepped/held rather than smoothly wandering) | [`pyo-api/control/randoms.py`](./pyo-api/control/randoms.py) | `pyo/lib/randoms.py` | `Randi`, `Randh`, `Choice`, `RandInt`, `RandDur`, `Xnoise`/`XnoiseMidi`/`XnoiseDur`, `Urn`, `LogiMap` |
| Exposing a musically-named high-level parameter (e.g. "brightness") that maps onto a low-level Pyo range | [`pyo-api/control/value_converters.py`](./pyo-api/control/value_converters.py) | `pyo/lib/_maps.py` | `Map`, `SLMap`, `SLMapFreq`, `SLMapMul`, `SLMapPhase`, `SLMapPan`, `SLMapQ`, `SLMapDur` |
| Reading MIDI note/controller/pitch-bend/aftertouch/program-change from an external device | [`pyo-api/external_io/midi.py`](./pyo-api/external_io/midi.py) | `pyo/lib/midi.py` | `Notein`, `Midictl`, `CtlScan(2)`, `Bendin`, `Touchin`, `Programin`, `MidiAdsr`/`MidiDelAdsr`/`MidiLinseg`, `RawMidi` |
| Background-thread MIDI/OSC event listening (as opposed to the audio-rate objects above) | [`pyo-api/external_io/listener.py`](./pyo-api/external_io/listener.py) | `pyo/lib/listener.py` | `MidiListener`, `MidiDispatcher`, `OscListener` |
| Sending/receiving control data over a network (OSC) | [`pyo-api/external_io/opensndctrl.py`](./pyo-api/external_io/opensndctrl.py) | `pyo/lib/opensndctrl.py` | `OscSend`/`OscReceive`, `OscDataSend`/`OscDataReceive`, `OscListReceive` |
| Playing back recorded audio, with pitch/speed control or marker-based looping | [`pyo-api/playback_routing/players.py`](./pyo-api/playback_routing/players.py) | `pyo/lib/players.py` | `SfPlayer`, `SfMarkerShuffler`, `SfMarkerLooper` |
| Panning, mixing, crossfading, voice management across channels | [`pyo-api/playback_routing/pan.py`](./pyo-api/playback_routing/pan.py) | `pyo/lib/pan.py` | `Pan`, `SPan`, `Switch`, `Selector`, `VoiceManager`, `Mixer` |
| Binaural/HRTF spatialization | [`pyo-api/playback_routing/hrtf.py`](./pyo-api/playback_routing/hrtf.py) | `pyo/lib/hrtf.py` | `HRTF`, `Binaural` |
| Storing 2D data (e.g. a sonogram) — the 2D equivalent of a table | [`pyo-api/playback_routing/matrix.py`](./pyo-api/playback_routing/matrix.py) | `pyo/lib/matrix.py` | `NewMatrix` |
| Recording into or reading/scanning a `NewMatrix` for granular/scanned synthesis | [`pyo-api/playback_routing/matrixprocess.py`](./pyo-api/playback_routing/matrixprocess.py) | `pyo/lib/matrixprocess.py` | `MatrixRec`/`MatrixRecLoop`, `MatrixPointer`, `MatrixMorph` |
| Frequency-domain (FFT) processing, convolution reverb | [`pyo-api/spectral/fourier.py`](./pyo-api/spectral/fourier.py) | `pyo/lib/fourier.py` | `FFT`/`IFFT`, `CarToPol`/`PolToCar`, `FrameDelta`/`FrameAccum`, `Vectral`, `CvlVerb`, `IFFTMatrix` |
| Higher-level spectral manipulation — time-stretch, pitch-shift, cross-synthesis, spectral gating/morphing | [`pyo-api/spectral/pvoc.py`](./pyo-api/spectral/pvoc.py) | `pyo/lib/phasevoc.py` | `PVAnal`/`PVSynth`/`PVAddSynth`, `PVTranspose`, `PVVerb`, `PVGate`, `PVCross`, `PVMorph`, `PVFilter`, `PVDelay`, `PVBuffer`/`PVBufLoops`/`PVBufTabLoops`, `PVShift`, `PVAmpMod`/`PVFreqMod`, `PVMix` |
| Callback-driven pattern/score sequencing | [`pyo-api/sequencing/pattern.py`](./pyo-api/sequencing/pattern.py) | `pyo/lib/pattern.py` | `Pattern`, `Score`, `CallAfter` |
| High-level, Python-side event/instrument scheduling framework | [`pyo-api/sequencing/events_framework.py`](./pyo-api/sequencing/events_framework.py) | `pyo/lib/events.py` | `Events`, `EventGenerator` and its subclasses (`EventSeq`, `EventMarkov`, `EventChoice`, `EventDrunk`, `EventNoise`, `EventSlide`, `EventIndex`, `EventCall`, `EventConditional`, `EventFilter`, `EventDummy`), `EventScale`, `EventInstrument`/`DefaultInstrument`, `MarkovGen` |
| Music Macro Language (MML) string-driven sequencing | [`pyo-api/sequencing/mml.py`](./pyo-api/sequencing/mml.py) | `pyo/lib/mmlmusic.py` | `MML` |

## Worked examples already in this codebase

Reading a working patch is often faster than reasoning from the table above. `src/pyoscillate/patches/`:

- `drone.py` — continuous, non-triggered modulation: two independent `Sine` LFOs at different sub-audio periods drift an `FM` voice's ratio and index, decoupled from the pitch-change schedule. The textbook case of `generators.py`'s "runs forever, feeding another object's parameter" (`LFO`/`Rossler`/`Lorenz` family).
- `clock_tick.py` — the reference implementation for "mechanical, unsynced, ticking" texture (this is literally the Pink Floyd *Time* clock-shop pattern): four independent `Metro`s at unrelated real-second periods (not tempo-locked), each feeding a `TrigEnv`/`Noise` pair band-shaped by `ButHP`/`ButBP`/`ButLP` to a different resonant frequency. Deliberately *not* using one shared clock is what makes it read as "a room of clocks that were never wound together" rather than a groove element.
- `bass.py` — a continuous modulator (LFO) sweeping a resonant lowpass filter cutoff, layered under a triggered 16-step sequence — shows continuous and event-driven modulation stacked on the same voice.
- `atmosphere.py` — an `FM` pad arpeggiated on the shared clock with a slow envelope-driven amplitude swell plus reverb — a case where the "evolving" quality comes from a slow envelope, not a modulator.
- `hat.py` / `low_hat.py` — minimal trigger → `TrigEnv` → filtered noise chains; the simplest possible instance of the core signal chain.
- `base.py` — every patch's shared tail: boost → `Compress` → fade → `.out()`. Read this before adding a new patch so gain-staging and clean start/stop aren't reinvented per-patch.

When a request resembles one of these, prefer adapting the existing pattern over designing a new one from scratch.

## Reference-track requests

For "make something inspired by [a recording/artist/scene]," do **not** jump straight to this file. The chain is:

```
reference track
    → references/research/reference-track-digging.md (extract characteristics, not a recipe)
    → the relevant genre/production-aware reference for context
    → back to this file, to pick synthesis mechanisms for the extracted characteristics
```

`clock_tick.py` above is the existing example of this having already been done once for "the ticking clocks in Pink Floyd's *Time*": the sonic characteristics (several unsynchronized periodic ticks, each a different resonant timbre, mechanical rather than musical) were identified first, and the free-running-`Metro`-per-voice architecture followed from that — the code was never written by looking up "Pink Floyd" anywhere. Use the same method for a new reference rather than copying that patch's numbers.

## A note on candidates, not answers

Every "what synthesis need" row above intentionally offers more than one file or class where more than one exists. This table narrows a large API down to a short list — it does not make the final choice. Which candidate fits depends on the specific character the musical/sonic reasoning layer decided on (e.g. "smooth wander" vs. "angular wander," "gated per-note" vs. "free-running"); keep that ambiguity alive until you've read the actual docstrings and picked based on documented behaviour, not the name of the class.

## Gaps / manual follow-up

- `analysis/`, `spectral/`, `sequencing/`, `external_io/`, `playback_routing/`, and `control/` are "not used by this project yet" — the mapping above is based on reading their documented behaviour, not on any existing patch using them. If one of these turns out not to fit a real request as well as expected, treat that as a signal to refine this table, not to force the fit.
- `pyo-api/` now documents every real Pyo object exposed by the installed `pyo` package (generated from its actual docstrings/signatures, one reference file per `pyo/lib/*.py` source module — verify this is still true after a `pyo` upgrade by diffing `grep -rn '^class ' <pyo install>/lib/*.py` against `grep -rhoE "^from pyo import \w+" pyo-api/` in this skill). GUI-toolkit classes (`_tkwidgets.py`, `_wxwidgets.py`) and internal base classes (`PyoObject`, `PyoTableObject`, `PyoMatrixObject`, `PyoPVObject`, `Clean_objects`) are intentionally excluded — they're not objects a patch instantiates directly.
- This file was written from the current `references/pyo-api/` contents. If that directory's files are added to or edited, this table needs a corresponding manual update — nothing here is generated.
