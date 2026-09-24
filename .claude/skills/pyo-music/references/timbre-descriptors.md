# Timbre Descriptors

Use this reference when a brief or a control label uses a perceptual word
("bright", "warm", "metallic", "punchy"). It sits between SONIC INTENT and DSP
MECHANISM in the chain described in [`../SKILL.md`](../SKILL.md). It exists so
that "don't map words directly to Pyo objects" has a positive alternative.

Each descriptor links a word to **what the listener hears**, **something you
can measure in the signal**, and **several unrelated ways to produce it**.
Pyo object names are pointers into [`pyo-api/`](./pyo-api/). They are not the
meaning of the word. No descriptor below is owned by a single object.

## How to use an entry

```
descriptor
    ↓
perception        what the listener hears
    ↓
correlate         what changes in the signal, and how to measure it
    ↓
mechanisms        2–4 different ways to produce it (pick by musical role)
    ↓
context           when the mapping breaks or means something else
```

1. Find the descriptor, or the closest one, and read **Often confused with**.
   Briefs often use one word for another.
2. Choose a mechanism based on the patch's family and role, not on which one
   is listed first. The mechanisms are unordered. Often the best answer
   combines two small moves instead of pushing one move hard.
3. Use the correlate for two things: to write the control's help text ("what
   will I hear if I move this?"), and to check the rendered result (see the
   render-and-verify task in
   [`docs/todos/synth-patch-ai-gist.md`](../../../../docs/todos/synth-patch-ai-gist.md)).
4. If a word isn't listed, build an entry the same way. Don't fall back to a
   single object.

## Correlates and how to measure them

| Correlate | What it measures | Native Pyo measurement |
|---|---|---|
| Spectral centroid | The "centre of mass" of the spectrum in Hz. Higher usually reads as brighter. | `Centroid` ([analysis.py](./pyo-api/analysis/analysis.py)) |
| Centroid ÷ f0 | Brightness relative to pitch. It stops a high note from counting as a bright timbre. | `Centroid` and `Yin` together |
| Amplitude envelope | Level over time: attack, decay, sustain, release | `Follower`, `PeakAmp` |
| Attack time / onsets | How fast the sound arrives; where the transients are | `AttackDetector`, or the slope of `Follower` |
| Decay time | Time to fall a fixed amount (for example −40 dB) after the peak or the note-off | `Follower` plus `AToDB` ([utils.py](./pyo-api/analysis/utils.py)) |
| Pitch and stability | f0 and how much it wanders or jumps | `Yin` |
| Harmonicity | Whether the partials sit on integer multiples of f0 | None. Inspect by eye with `Spectrum`, or run an offline FFT |
| Even/odd balance, notches | Which harmonics are present or missing | None. Inspect with `Spectrum`, or run an offline FFT |
| Crest factor | Peak level ÷ RMS. It falls as a sound gets more compressed or distorted. | `PeakAmp` and `Follower`, roughly |
| Stereo correlation | How similar L and R are (1 = mono, 0 = decorrelated) | None. Needs offline analysis |

numpy is not a project dependency yet. Task 2 of the todo decides whether the
non-native measurements are worth adding it.

## Spectral balance

### bright
- **Perception:** open, present, forward, cutting.
- **Correlate:** higher centroid, and more energy well above the fundamental. Judge it as centroid ÷ f0, not raw Hz.
- **Mechanisms:**
  - Open a low-pass, or sweep it with an envelope (`MoogLP`, `SVF`, `ButLP`).
  - Start from a source rich in harmonics (saw or pulse, `Blit` with more harmonics, `SuperSaw`).
  - Raise the FM index (`FM`).
  - Add harmonics with saturation or waveshaping (`Disto`, or `Lookup` over a `ChebyTable`).
- **Context:**
  - Noise raises the centroid without sounding musically bright. It reads as hiss or air.
  - In a dense mix, "bright" is often really "less masked". The fix may be to cut other parts, not to boost this one.
- **Often confused with:** harsh (energy concentrated around 2–5 kHz), airy, loud.

### dark
- **Perception:** muted, soft, distant, heavy, closed.
- **Correlate:** low centroid ÷ f0, with little energy above the first few harmonics.
- **Mechanisms:**
  - Close the low-pass, or use a gentle `Tone` roll-off.
  - Use a source with few harmonics (`Sine`, triangle, or `SineLoop` with low feedback).
  - Play in a lower register.
  - Damp delay/reverb feedback (a filter inside the feedback path; `Freeverb` `damp`, `WGVerb`/`STRev` `cutoff`).
- **Context:**
  - Removing all high frequencies also removes articulation. A dark bass or kick often still needs a small upper-harmonic or transient layer so it reads on small speakers.
  - Dark plus reverb reads as distant. Dark plus close and dry reads as muffled.
- **Often confused with:** warm, low, sad (a musical judgement about mode or harmony, not timbre).

### warm
- **Perception:** full, rounded, "analog", comfortable. Never piercing.
- **Correlate:**
  - moderate centroid ÷ f0
  - energy weighted to the low mids for the register
  - a soft high-frequency slope, not a hard cutoff
  - slight pitch and amplitude instability
- **Mechanisms:**
  - Gentle saturation that adds low-order harmonics (`Disto` at low drive, or `Lookup` over a low-order `ChebyTable`).
  - Slow, very small pitch drift (`Randi` into frequency, a few cents).
  - A gentle low-pass with a soft slope (`Tone`, or `MoogLP` with low resonance).
  - A small amount of unison detune.
- **Context:**
  - "Warm" usually means instability plus a soft top, not a bass boost.
  - Too much low-mid is muddy, especially on stacked chords.
  - Heavy detune reads as wide or chorused, not warm.
- **Often confused with:** dark, bassy, lo-fi.

### airy
- **Perception:** breath, shimmer, openness above the tone.
- **Correlate:** low-level, noise-like energy in the very top band (roughly above 6–8 kHz) that follows the note.
- **Mechanisms:**
  - Layer noise, high-passed or band-passed (`Noise`/`PinkNoise` → `ButHP`/`ButBP`), driven by the same amplitude envelope.
  - Boost a high shelf on a source that already has top end (`EQ`).
  - Use bright, diffuse reverb with a short pre-delay (`STRev` with a high `cutoff`, `Freeverb` with low `damp`).
- **Context:**
  - Air is quiet. As soon as it is audible as a separate hiss, it has become a noise layer.
  - Energy around 2–5 kHz is harshness, not air.
- **Often confused with:** bright, breathy (vocal), reverb.

### hollow
- **Perception:** woody, nasal, clarinet-like, or "boxy". Something is missing from the middle of the sound.
- **Correlate:** missing even harmonics, or regular dips (notches) in the spectrum.
- **Mechanisms:**
  - Use a square or 50 % pulse source, which has odd harmonics only (`LFO` with `type=2`, which is band-limited despite the name).
  - Use FM with a 1:2 carrier:modulator ratio, which produces odd harmonics only.
  - Comb-filter with a short delay mixed against the dry signal (`Delay`, very short time). This produces regular notches.
  - Use band-pass or formant resonances that skip the fundamental region (`Reson`, `Resonx`).
- **Context:** hollow and nasal overlap. Formant-like peaks read as vocal or nasal. Regular notches read as phasey or boxy.
- **Often confused with:** thin, phased.

## Spectral structure

### metallic
- **Perception:** clang, ring, bell, gong, struck metal.
- **Correlate:** inharmonic partials, often dense, often decaying at different rates.
- **Mechanisms:**
  - FM with a non-integer ratio (`FM`, for example ratio 1.4 or 3.5).
  - A bank of resonators tuned to inharmonic frequencies (`Resonx`, `ComplexRes`, or several `Waveguide`s) excited by noise or a click.
  - Ring modulation: multiply two oscillators that are not harmonically related.
  - Short comb delays with high feedback (`Waveguide`, `Delay`), or a frequency shift (`FreqShift`) to break harmonicity.
- **Context:**
  - Inharmonic with a short decay reads as clank or percussion. With a long decay it reads as bell or gong. The envelope carries half the meaning.
  - Unintended metallic colour comes from short comb or reverb resonances (see the Valhalla notes in [`docs/todos/sources.md`](../../../../docs/todos/sources.md)).
- **Often confused with:** bright, harsh, glassy.

### glassy
- **Perception:** clean, pure, crystalline, chime-like. Fragile.
- **Correlate:** a few clear partials, with high partials present but sparse. Clean onset, little noise, a smooth decay.
- **Mechanisms:**
  - Low-index FM with a high ratio (a few sidebands only).
  - Additive synthesis of a few partials (`OscBank`, or `HarmTable` into an oscillator).
  - A sine or `SineLoop` exciting a high-Q resonance.
- **Context:** glassy is to metallic what a few partials are to many. Raising the index or adding partials pushes glassy toward metallic.
- **Often confused with:** metallic, bright, bell.

### distortion / driven
- **Perception:** thick, aggressive, saturated, edgy.
- **Correlate:** added harmonics, a higher centroid, and a lower crest factor (peaks flattened).
- **Mechanisms:**
  - Soft waveshaping (`Disto`, or `Lookup` + `ChebyTable`).
  - Hard clipping (`Clip`).
  - Wavefolding (`Mirror`, `Wrap`).
  - Very high FM index.
- **Context:**
  - The position in the chain matters. Distortion *after* the filter keeps the filter's sweep but adds edge (the TB-303 order). Distortion *before* the filter lets the filter tame it.
  - Chords distort into intermodulation mud. Distort single lines, or distort before the harmony is summed.
- **Often confused with:** gritty, loud, bright.

### gritty
- **Perception:** rough, crunchy, dirty, lo-fi texture.
- **Correlate:** noise or aliasing products that are not harmonic, and a grainy texture over time.
- **Mechanisms:**
  - Bit and sample-rate reduction (`Degrade`).
  - Very fast random modulation of amplitude or pitch (`Randi` at audio-adjacent rates).
  - Noise modulated by the signal envelope.
  - Hard clipping plus band-limiting.
- **Context:** gritty is textural, while driven is harmonic. A brief asking for "dirty" often wants a little of both at low depth.
- **Often confused with:** distortion, noisy.

### multiphonic
- **Perception:** more than one pitch at once, or an unstable pitch identity: beating, subharmonics, a split tone.
- **Correlate:** several unrelated spectral peaks. `Yin` output jumps or does not settle.
- **Mechanisms:**
  - Cross-modulation (`CrossFM`).
  - Ring modulation.
  - Wide detune, or stacked non-octave intervals in one voice.
  - Chaotic oscillators used as the source or the modulator (`Lorenz`, `Rossler`, `ChenLee`).
- **Context:** this is the intent for drones and textures, but usually a bug in a lead or a bass. Check which the brief wants.
- **Often confused with:** detuned, chorused, dissonant (a harmony judgement).

## Envelope and time

### percussive
- **Perception:** struck or plucked. The sound arrives and leaves, with no held sustain.
- **Correlate:** a fast attack (roughly under 10 ms), no sustain stage, and an amplitude that decays steadily.
- **Mechanisms:**
  - A short amplitude envelope with zero sustain (`TrigEnv`, `Adsr` with sustain 0).
  - A noise or click transient layer.
  - A fast downward pitch envelope (`Expseg` into frequency).
  - A fast filter envelope that closes after the onset.
- **Context:** percussive does not mean drums. Plucks, keys and bells are percussive and tonal. Use the family rules in [`patches/CLAUDE.md`](../../../../src/pyoscillate/patches/CLAUDE.md) to place the patch.
- **Often confused with:** punchy, short.

### punchy
- **Perception:** impact, force, "hits you in the chest", tight.
- **Correlate:** a strong transient relative to the body in roughly the first 5–50 ms, a fast rise, and a controlled (not long) tail.
- **Mechanisms:**
  - A pitch envelope that drops into the body (`Expseg` into frequency).
  - A separate transient layer: click or filtered noise.
  - Compression with a slow attack, so the transient passes before gain reduction (`Compress`).
  - Saturation on the body, to hold its level after the transient.
- **Context:** punch comes from the transient-to-body relationship, and depends on the mix. A long tail or heavy reverb removes punch, even with a strong transient.
- **Often confused with:** loud, percussive, bright.

### fast_decay
- **Perception:** short, tight, dry, clipped.
- **Correlate:** a short time from the peak to −40 dB.
- **Mechanisms:**
  - A short amplitude decay or release.
  - A filter envelope that closes quickly, so the sound darkens as it fades.
  - Heavily damped resonators (a short `Waveguide` duration).
  - Gating.
- **Context:**
  - Closing the filter fast sounds different from shortening the amplitude: the note keeps its length but loses its tone.
  - A decay that is too short on a pitched voice loses pitch clarity.
- **Often confused with:** percussive, staccato (a playing articulation, not a timbre).

### long_release
- **Perception:** the note hangs on after it ends.
- **Correlate:** a long time from note-off to −40 dB.
- **Mechanisms:**
  - A long envelope release (`Adsr`).
  - A long resonator decay.
  - A delay or reverb tail.
- **Context:**
  - An envelope release keeps the *source* sounding: its pitch stays clear. A reverb tail is diffuse: pitch and definition blur.
  - Overlapping releases smear harmony and rhythm. That's fine for pads, bad for basslines.
- **Often confused with:** reverb, sustain.

### nonlinear_env
- **Perception:** the level or tone moves within a single note: swells, pumps, flutters, blooms.
- **Correlate:** an amplitude or centroid curve that is not monotonic, with several stages or periodic movement.
- **Mechanisms:**
  - Multi-stage envelopes (`Expseg` with several breakpoints).
  - An LFO on amplitude (tremolo) or on the filter.
  - Compressor or sidechain pumping.
  - An envelope follower on one voice modulating another (`Follower` → a parameter).
- **Context:** the timescale changes the meaning. See "Modulation and timescale" in [`../SKILL.md`](../SKILL.md).
- **Often confused with:** tempo-synced, unstable.

## Space and width

### reverb / spacious
- **Perception:** a room around the sound. Distance, size, diffusion.
- **Correlate:** energy continues after the direct sound, and the direct-to-reverberant ratio is lower.
- **Mechanisms:**
  - Algorithmic reverb (`Freeverb`, `STRev`, `WGVerb`).
  - Early reflections from short multi-tap delays.
  - A pre-delay before the reverb (`Delay`), to keep the source clear while it sits in space.
  - Damped tails, so distance also darkens the sound.
- **Context:**
  - Distance needs a lower direct level and less high-frequency content as well as more reverb.
  - Reverb reduces rhythmic definition. Use pre-delay, or a shorter decay, on rhythmic parts.
- **Often confused with:** long_release, wide, ambient (not a family; see [`patches/CLAUDE.md`](../../../../src/pyoscillate/patches/CLAUDE.md)).

### wide
- **Perception:** fills the stereo field. Enveloping, not coming from one point.
- **Correlate:** low correlation between L and R.
- **Mechanisms:**
  - Detuned voices panned apart (`SPan`/`Pan` per voice). `SuperSaw` detune alone is a mono stack, so pan separate instances.
  - Chorus (`Chorus`).
  - A short delay between L and R (the Haas effect, roughly under 30 ms).
  - Independent slow random modulation per channel.
- **Context:**
  - Check the mono fold-down: Haas and wide chorus can cancel in mono.
  - Keep sub and bass content near mono.
- **Often confused with:** reverb, big, loud.

## Time and rhythm

### tempo-synced
- **Perception:** movement that locks to the groove: gated, pulsing, rhythmic filter motion.
- **Correlate:** modulation of amplitude or centroid that repeats with the beat grid.
- **Mechanisms:**
  - An LFO rate derived from tempo (Hz = BPM ÷ 60 × multiplier).
  - Clock-driven retriggering of envelopes.
  - Delay times in beats.
  - Gated noise or amplitude patterns.
- **Context:** timing parameters have state rules in this codebase. See rule 5, "Keep timing/state explicit", in [`patches/CLAUDE.md`](../../../../src/pyoscillate/patches/CLAUDE.md) before exposing a synced rate as a live slider.
- **Often confused with:** nonlinear_env, rhythmic (a musical judgement about the part).

## Sources

- NSynth quality labels (bright, dark, distortion, fast_decay, long_release,
  multiphonic, nonlinear_env, percussive, reverb, tempo-synced):
  https://magenta.tensorflow.org/datasets/nsynth
- Roche et al., "Make That Sound More Metallic: Towards a Perceptually
  Relevant Control of the Timbre of Synthesizer Sounds Using Variational
  Autoencoder" (TISMIR 2021). Dataset: https://zenodo.org/records/4680486
- Found through the [0xdevalias synth-patch gist](https://gist.github.com/0xdevalias/5a06349b376d01b2a76ad27a86b08c1b).
  See [`docs/todos/synth-patch-ai-gist.md`](../../../../docs/todos/synth-patch-ai-gist.md).
- FM ratio and index behaviour: see the bell sources in
  [`docs/todos/sources.md`](../../../../docs/todos/sources.md) (CCRMA,
  Cycling '74, Synth Secrets 40).
