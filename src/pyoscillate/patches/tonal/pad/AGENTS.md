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

## Subtractive pads

`pad.py` holds `SynthPad`, a `common.Held` voice (a `Reverb` and an `Ensemble` of detuned copies, so a chord shimmers) and the nine pads of the cookbook's pad section as styles of it. A pad plays the rack's chord on a chord rhythm (a bar-long pulse by default) and lets go over a long Release; Legato defaults to 0.9 so each chord is released a little before the next and its filter blooms again, where at 1 the chords slur into one another and the filter opens only once.

The graph is the classic subtractive recipe, the same for every style:

- **two oscillators** (saw, square or triangle) at their own pitch offsets and levels, plus **noise** (Air). A square is a sawtooth minus itself delayed by the pulse width (pyo's own pulse is not a duty-cycle square), so its width can sway. The second oscillator can be **hard-synced** to the first: it is read from a table at the first's phase times the pitch ratio, wrapped, so its pitch is the sweep of the sync tone;
- a **24 dB low-pass** (`MoogLP`) whose cutoff is the cookbook's knob, 20 Hz to 20 kHz across 0 to 1 on a log scale, so every recipe's figure carries over. Brightness is where it rests, Opening how far its own envelope swings it open on each chord, Resonance how it rings, and a style may make it follow the note (key tracking, which keeps a ringing wash's chord in tune);
- **one slow LFO** (Movement is its depth, Movement speed its rate) routed where the recipe says: the pulse width, the cutoff, the level, the second oscillator's pitch (the sync sweep) or the resonance;
- a slow amplitude envelope (Attack, Release, the style's own decay and sustain) and a room.

A style is only profile data: the oscillators' shapes, offsets and levels, the sync flag, the LFO's shape and its routings, the filter envelope's times, the amplitude decay and sustain, and its own starting values for the shared sliders.

| style | recipe | what you hear |
| --- | --- | --- |
| Android Dreams | square -2 oct, synced saw, noise; LFO on pulse, cutoff and the sync pitch | a swirling, breathy lullaby |
| Celestial Wash | noise only, resonance 100% pulsed by a square LFO, key tracking | a pitched wash that swells and fades while held |
| Dark City | square -2 oct, saw a seventh down; filter opens over five seconds | a looming bed that blooms and settles |
| Aurora | two squares ±10 cents, swaying pulse, ringing filter | a shimmering curtain |
| Galactic Cathedral | two squares, the second +2 oct, slow cutoff tide | vast and stone-ringing |
| Galactic Chapel | two triangles an octave apart, slow cutoff and level tide | hushed, soft, intimate |
| Portus | two triangles, 1.5 s glide between chords, slow filter bloom | drifting harbour lights |
| Post-Apocalyptic Sync Sweep | two squares hard-synced, pitch swinging ±4.5 semitones | a grinding, rusted sky |
| Terra Enceladus | saw over a square an octave down, swaying pulse | cold, glassy and alien |

What the cookbook recipes ask for that this does not do:

- the PWM LFO of a hard-synced pad moves only the master's pulse: the synced oscillator is read from a table, so its width is fixed;
- the recipes' LFO routings that share one rate (for example Android Dreams' pulse, cutoff and sync pitch) use that one rate, as the recipes do;
- the filter is `MoogLP`, which is unstable for a hot input at a high cutoff. The oscillators are trimmed before it and the cutoff stops at 10 kHz (see the findings in `tests/pyoscillate/patches/tonal/pad/test_pad.py`), so a pad is a little darker at the top than the recipe's 20 kHz.

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
