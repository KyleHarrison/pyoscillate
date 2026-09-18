brew update
brew reinstall flac
brew install ffmpeg
?

brew install liblo libsndfile portaudio portmidi

Here's the conceptual map — Pyo's classes fall into a handful of roles, and every patch is just wiring these roles together into a graph.

**1. Server** — the audio engine. One per program. Everything else needs it running to produce sound.

**2. Signal generators (sources)** — things that produce a raw waveform: `Sine`, `Osc` (plays a wavetable), `LFO`, `SuperSaw`, `FM`, noise generators (`Noise`, `PinkNoise`, `BrownNoise`). These are your starting sound.

**3. Tables** — not sound themselves, but shapes/data that generators read from: `SquareTable`, `SawTable`, `CosTable`, `CurveTable`. `Osc` needs a table to know what waveform to play.

**4. Triggers / event sources** — things that fire discrete pulses: `Metro` (steady clock), `Beat` (pattern clock), `Trig`. These don't make sound; they make *timing events* that other objects react to.

**5. Trig-reactive objects** — listen for a trigger and do something each time one arrives: `TrigEnv` (replay an envelope shape), `TrigXnoiseMidi` (pick a new random pitch), `TrigRand`. This is how "Metro fires → new note happens" gets wired up in your notebook.

**6. Envelopes / control signals** — shape a parameter over time, usually gated by a trigger or note-on: `Adsr`, `Fader`, `TrigEnv`. Used for one-shot shaping (a note's loudness contour).

**7. Modulators (continuous, non-triggered)** — `LFO`, `Sine` used at sub-audio rate, strange attractors (`Rossler`, `Lorenz`). These run forever, feeding another object's parameter (freq, amplitude, filter cutoff) to make it wobble/sweep continuously.

**8. Filters & effects** — process an existing signal: `Biquad`, `Tone`, `Disto`, `Freeverb`, `Delay`, `Chorus`. Take a signal in, transform it, pass a modified signal out.

**9. Output** — `.out()` sends a signal to the speakers. `.play()` starts an object's internal processing without sending audio out (used for triggers/envelopes that only exist to drive other objects).

**How they combine — the actual pattern in your notebook:**

```
Metro (timing) ──► TrigEnv (amplitude shape) ──┐
Metro (timing) ──► TrigXnoiseMidi (pitch)   ────┼──► Osc (generator) ──► .out()
```

The general template is always: **timing source → triggered control objects → parameters of a generator/effect → output.** Continuous modulators (LFOs) plug into the same parameter slots as triggered ones — the difference is just whether the modulation is event-driven (one-shot, gated) or free-running (cyclical, ungated).

Once you see every object as one of these roles — source, shaper/table, timing, trigger-reactive control, continuous modulator, filter, or sink — reading any Pyo patch becomes: trace each wire backward from `.out()` and ask "what role is feeding this parameter, and is it one-shot or continuous?"