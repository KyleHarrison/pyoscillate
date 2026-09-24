# Pad

## Sonic function

A pad is a sustained harmonic layer whose identity is defined by slow evolution, spectral motion, and the way the sound breathes over time. It is not simply a chord voice; it is a chord voice with a long temporal envelope and a nontrivial timbral evolution.

## Minimal architecture

oscillator(s)
→ harmonic voicing
→ slow amplitude envelope
→ filter movement or modulation
→ optional detuning and stereo spread
→ optional room reverb

## Core design idea

The pad is judged by:

- slow attack and long release
- voiced harmonic content
- detune or oscillator drift
- slow filter or waveform movement
- spatial openness

It should feel like a sustained layer that sits behind the melody or rhythm, not a transient sound.

## Parameter logic

The strongest controls are usually:

- voicing: the pitch content and harmonic density
- drift: slow movement in the harmonic structure
- brightness: how open or dark the pad feels
- space: how much diffusion/reverb gives it distance
- movement rate: how quickly timbre changes

## Design alternatives

Warm pad:
    restrained brightness + moderate detune + long release

Shimmer pad:
    brighter voicing + wider stereo + more high-end diffusion

Dark pad:
    low-pass contour + reduced upper harmonics + slower modulation

## What NOT to assume

A pad is not just a chord with a long envelope. The act of “breathing” and evolving over time is central to its identity. That movement often matters more than the exact oscillator choice.

## Musical references

These point to the music-theory layer for decisions *around* this voice
(pattern, pitch material, role in the arrangement and mix). They do not
cover synthesis; the sections above stay authoritative for the DSP.

- `.claude/skills/music-theory/references/orchestration/voicing-and-texture.md` — close vs. open, spread, quartal/quintal and cluster voicings (the "voicing" control)
- `.claude/skills/music-theory/references/harmony/voice-leading.md` — for smooth motion between chords so a sustained pad doesn't jump
- `.claude/skills/music-theory/assets/jazz-voicings.md` — open and quartal voicings suit slow pads
- `.claude/skills/music-theory/assets/progressions-catalog.md` and `modes-cheatsheet.md` (same folder) — for harmonic material and mode colour
- `.claude/skills/music-theory/references/instrument-idiom/piano-keyboards.md` — "Synth/key pad" and "Voicing rules of thumb"
- `.claude/skills/pyo-music/references/pitch-and-harmony-implementation.md` — how to sound several pitches at once once the voicing is chosen
- `.claude/skills/music-theory/references/production-aware/arrangement-for-mix.md` — "Stereo space" and "The mid-range problem", for keeping the pad behind melody and rhythm
