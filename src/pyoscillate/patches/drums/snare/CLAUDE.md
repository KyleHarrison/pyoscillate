# Snare

## Sonic function

A snare combines a short pitched drum body with a brighter noisy rattle. The
body gives the hit a center and weight; the noise gives it width, articulation,
and the characteristic wire-like tail.

## Minimal architecture

trigger
→ tonal oscillator
→ body envelope
→ body mix

trigger
→ noise generator
→ high-pass or band-pass filter
→ noise envelope
→ body/noise mix

## Tonal body

Use a pitched oscillator at a higher register than a kick. A modest downward
pitch gesture can add impact, but the sweep should be less pronounced than on a
kick so the sound does not become a zap or tom.

## Noise component

The noise is usually the louder component. High-pass filtering removes low
energy that would compete with the kick, while moderate resonance can give the
tail a defined rattling character.

## Amplitude envelope

Keep the attack at zero for a sharp hit. A shorter decay gives a dry, direct
snare; a longer, strongly exponential decay leaves a noisy tail that can read
like a small room around the hit.

## Design alternatives

Dry snare:
    short tonal body + short filtered-noise decay

Roomy snare:
    restrained body + longer exponential noise tail

Zap-like percussion:
    tonal oscillator + stronger pitch envelope + little or no noise

## What NOT to assume

Do not assume that every snare needs equal tone and noise, a fixed pitch, or a
long tail. The balance is style- and arrangement-dependent.

## Musical references

These point to the music-theory layer for decisions *around* this voice
(pattern, pitch material, role in the arrangement and mix). They do not
cover synthesis; the sections above stay authoritative for the DSP.

- `.claude/skills/music-theory/references/instrument-idiom/drums-percussion.md` — "Backbeat", "Half-time" and "Fill design", for where the snare lands
- `.claude/skills/music-theory/references/rhythm-groove/groove-and-feel.md` — "Ghost notes" and "Velocity and dynamic accents within a groove", for secondary, quieter hits
- `.claude/skills/music-theory/references/production-aware/arrangement-for-mix.md` — "The frequency spectrum" and "The mid-range problem", for balancing body pitch and noise band against other voices
