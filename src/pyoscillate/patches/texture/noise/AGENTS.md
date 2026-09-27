# Noise

## Sonic function

A filtered-noise layer is the simplest texture: a broadband source whose character is set entirely by its colour, its filtering and the way those move. The same source can be air, hiss, surf or wind depending on shaping. Because noise has no pitch centre, all of its identity is spectral balance and motion.

## Minimal architecture

noise source (white / pink / brown, crossfaded)
→ low-pass (how much hiss survives)
    ↑ slow modulation
→ movement stage (cutoff breathing, notch sweep or frequency shift)
→ level
→ optional spatial treatment

## Colour

The three classic colours differ only in how energy falls with frequency:

- white: equal energy per Hz, so it sounds bright and hissy
- pink: equal energy per octave (−3 dB/octave), which sounds balanced and "natural", like surf or rain
- brown: −6 dB/octave, dark and rumbling, like distant wind or a river

A continuous crossfade between them (pyo's `Selector`, as in example x03/04) makes colour one perceptual control instead of a switch. The low-pass then trims whatever top end the colour leaves.

Perceptual:

- whiter → closer, airier, more present, and more likely to mask a lead or vocal
- browner → further away, heavier, and easy to lose under bass

## Movement

A still noise bed is a test signal. The interest comes from slow movement, and each kind of movement reads differently:

- **Cutoff breathing.** The low-pass cutoff swells on slow LFOs. The bed opens and closes like wind gusting. Using unrelated rates per channel stops the left and right sides from ever moving together.
- **Notch sweep (phaser).** Many notches (x06/04 uses 20) sweep through pink noise. Each notch position, spacing and sharpness rides its own slow LFO per channel. Moving notches through a dense spectrum give the hollow, whooshing motion of surf. A phaser's notches come from summing a phase-shifted copy with the dry signal: pyo's `Phaser` is an allpass cascade, so its output alone has a flat spectrum and must be mixed with the dry bed.
- **Frequency shift.** A single-sideband shift (Hilbert transform plus a quadrature sine, x06/07) moves every partial by a fixed number of Hz. A few Hz of slowly varying shift, mixed with the dry bed, beats against it and gives a slow swirl that never settles. A separate shift per channel makes the swirl travel across the stereo field.

Increasing:

- rate → from tide-like to fluttering; past about 1 Hz the movement starts to read as a rhythm
- depth → from a barely-moving bed to an obvious sweep

## Design alternatives

Air / wind:
    pink or brown noise + low-pass whose cutoff breathes on slow unrelated LFOs

Surf:
    pink noise + many-notch phaser with independent slow LFOs per channel

Swirl:
    noise + slowly varying frequency shift mixed with the dry bed, per channel

## What NOT to assume

- Colour and brightness are not the same control. Colour tilts the whole spectrum; brightness only removes the top. A brown bed with an open filter still sounds dark.
- Faster modulation doesn't mean more movement. Past a certain rate the ear hears flutter, not motion.
- The loudest colour is not constant. Low-passed white noise loses more energy than brown, so a colour control has to keep loudness roughly steady.

## Boundaries

An ungated noise bed is texture. A gated noise sweep used to mark a section change belongs in `transition/`; a noise hit on the grid belongs in `drums/`.

## Musical references

These point to the music-theory layer for decisions *around* this voice
(pattern, pitch material, role in the arrangement and mix). They do not
cover synthesis; the sections above stay authoritative for the DSP.

- `.claude/skills/music-theory/references/orchestration/arrangement-density.md`
- `.claude/skills/music-theory/references/production-aware/arrangement-for-mix.md` — keeping hiss out of the vocal/lead band

## Sources

pyo examples x03/04 (noise generators), x06/04 (phasing) and x06/07 (Hilbert transform), pyo 1.0.6 documentation.
