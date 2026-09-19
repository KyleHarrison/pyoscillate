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

| Synthesis need | Category | File | What's inside (read the file for real params) |
|---|---|---|---|
| A raw sound source — pitched oscillator, wavetable, or noise | Generators | [`core/02_generators.py`](./pyo-api/core/02_generators.py) | `Sine`, `Osc`, `LFO`, `SuperSaw`, `FM`, `Noise`, `PinkNoise`, `BrownNoise` |
| A precomputed shape/waveform/curve for a generator or envelope to read | Tables | [`core/03_tables.py`](./pyo-api/core/03_tables.py) | `SquareTable`, `SawTable`, `CosTable`, `CurveTable` |
| Discrete rhythmic pulses — a clock, an algorithmic pattern, a one-shot trigger | Triggers / event sources | [`core/04_triggers.py`](./pyo-api/core/04_triggers.py) | `Metro` (isochronous), `Beat` (weighted/algorithmic pattern), `Trig` (one-shot) |
| Something that reacts fresh each time a trigger fires (new envelope shape, new random value per hit) | Trig-reactive | [`core/05_trig_reactive.py`](./pyo-api/core/05_trig_reactive.py) | `TrigEnv`, `TrigXnoiseMidi`, `TrigRand` |
| A one-shot amplitude/parameter shape gated by a note or trigger | Envelopes | [`core/06_envelopes.py`](./pyo-api/core/06_envelopes.py) | `Adsr`, `Fader` |
| Continuous, free-running, **ungated** movement in a parameter — the opposite of trig-reactive | Modulators | [`core/07_modulators.py`](./pyo-api/core/07_modulators.py) | `Sine`/`LFO` at sub-audio rate for periodic movement; `Rossler`/`Lorenz` chaotic attractors for smoothly wandering, never-repeating "organic" movement — the file's own docstrings distinguish their character |
| Reshaping an existing signal's spectrum or texture — filtering, distortion, reverb, delay, chorus | Filters & effects | [`core/08_filters_effects.py`](./pyo-api/core/08_filters_effects.py) | `Biquad`, `Tone`, `Disto`, `Freeverb`, `Delay`, `Chorus` |
| Managing loudness/level range rather than spectrum (limiting, gating, clipping, folding) | Dynamics | [`core/09_dynamics.py`](./pyo-api/core/09_dynamics.py) | `Compress`, `Gate`, `Clip`, `Mirror`, `Wrap`, `Balance`, `Expand`, `Min`, `Max` |
| Sending a finished signal to speakers | Output | [`core/10_output.py`](./pyo-api/core/10_output.py) | `.out()` / `.play()` — methods on every `PyoObject`, not a separate class |

**Continuous vs. trig-reactive is the single most important distinction to get right** when a description implies "movement" or "change." Ask: is the change one-shot and tied to a discrete event (→ `05_trig_reactive.py` / `06_envelopes.py`), or ongoing and ungated (→ `07_modulators.py`)? Both plug into the same parameter slots on a generator or filter — the difference is purely in what drives them.

## Beyond the core chain — not yet used in this project's patches, still fully documented

These are real, available categories; "not used yet" in their docstrings means no existing patch happens to need them, not that they're unavailable or unreliable.

| Synthesis need | File | What's inside |
|---|---|---|
| Measuring an existing signal instead of generating one — envelope following, pitch tracking, brightness/onset detection | [`pyo-api/analysis/signal_analysis.py`](./pyo-api/analysis/signal_analysis.py) | `Follower`, `Yin`, `RMS`, `Centroid`, `AttackDetector` |
| Per-sample math or a small text-based DSP expression language | [`pyo-api/analysis/arithmetic.py`](./pyo-api/analysis/arithmetic.py), [`pyo-api/analysis/expression.py`](./pyo-api/analysis/expression.py) | `Sin`/`Log`/`Abs`/`Pow`/`Round`; `Expr` |
| Unit conversion, freezing a continuous signal into stepped values, recording to disk | [`pyo-api/analysis/utils.py`](./pyo-api/analysis/utils.py) | `Scale`, `SampHold`, `Interp`, `MToF`, `Record` |
| Free-running random values as an alternative flavor of continuous modulation (stepped/held rather than smoothly wandering) | [`pyo-api/control/randoms.py`](./pyo-api/control/randoms.py) | `Choice`, `Randh`, `Xnoise`, `Urn` |
| Exposing a musically-named high-level parameter (e.g. "brightness") that maps onto a low-level Pyo range | [`pyo-api/control/value_converters.py`](./pyo-api/control/value_converters.py) | `SLMap`, `SLMapFreq`, `SLMapQ` |
| Reading MIDI note/controller/pitch-bend from an external device | [`pyo-api/external_io/midi.py`](./pyo-api/external_io/midi.py), [`pyo-api/external_io/listeners.py`](./pyo-api/external_io/listeners.py) | `Notein`, `Midictl`, `Bendin`, `MidiAdsr`, `MidiListener` |
| Sending/receiving control data over a network | [`pyo-api/external_io/opensndctrl.py`](./pyo-api/external_io/opensndctrl.py) | `OscSend`, `OscReceive`, `OscDataSend` |
| Playing back recorded audio, with pitch/speed control or marker-based looping | [`pyo-api/playback_routing/players.py`](./pyo-api/playback_routing/players.py) | `SfPlayer`, `SfMarkerLooper`, `SfMarkerShuffler` |
| Panning, mixing, crossfading, or binaural placement across channels | [`pyo-api/playback_routing/routing.py`](./pyo-api/playback_routing/routing.py) | `Mixer`, `Pan`, `SPan`, `Selector`, `Switch`, `Binaural` |
| Storing/reading 2D data (e.g. a sonogram) — the 2D equivalent of a table, for granular/scanned synthesis | [`pyo-api/playback_routing/matrix.py`](./pyo-api/playback_routing/matrix.py) | `NewMatrix`, `MatrixPointer`, `MatrixRec`, `MatrixMorph` |
| Frequency-domain processing, convolution reverb | [`pyo-api/spectral/fourier.py`](./pyo-api/spectral/fourier.py) | `FFT`, `IFFT`, `PolToCar`, `CvlVerb` |
| Higher-level spectral manipulation — time-stretch, pitch-shift, cross-synthesis (morphing between two sounds' spectra) | [`pyo-api/spectral/pvoc.py`](./pyo-api/spectral/pvoc.py) | `PVAnal`, `PVSynth`, `PVTranspose`, `PVMorph` |
| Declarative/algorithmic note sequencing beyond raw `Metro`/`Trig` wiring | [`pyo-api/sequencing/event_sequencing.py`](./pyo-api/sequencing/event_sequencing.py), [`pyo-api/sequencing/events_framework.py`](./pyo-api/sequencing/events_framework.py), [`pyo-api/sequencing/mml.py`](./pyo-api/sequencing/mml.py) | `Pattern`, `CallAfter`, `Score`; `Events`, `EventSeq`, `EventMarkov`, `EventScale`; `MML` |

## Worked examples already in this codebase

Reading a working patch is often faster than reasoning from the table above. `src/pyoscillate/patches/`:

- `drone.py` — continuous, non-triggered modulation: two independent `Sine` LFOs at different sub-audio periods drift an `FM` voice's ratio and index, decoupled from the pitch-change schedule. The textbook case of `07_modulators.py`'s "runs forever, feeding another object's parameter."
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

- `analysis/`, `spectral/`, `sequencing/`, `external_io/`, `playback_routing/`, and `control/` are marked "not used by this project yet" in their own docstrings — the mapping above is based on reading their documented behaviour, not on any existing patch using them. If one of these turns out not to fit a real request as well as expected, treat that as a signal to refine this table, not to force the fit.
- This file was written from the current `references/pyo-api/` contents. If that directory's files are added to or edited, this table needs a corresponding manual update — nothing here is generated.
