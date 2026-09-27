# Cymbal

## Sonic function

A cymbal is a bright, inharmonic burst with a longer, diffuse decay than a
hi-hat. It supplies transition energy, sustained top-end motion, or a broad
accent above the rhythmic grid.

## Minimal architecture

trigger
→ complex metallic/noisy source
→ band-pass filter
→ long amplitude envelope
→ output

Optional:
→ slow filter modulation
→ saturation

## Source spectrum

Several high-frequency oscillators with modulation can create a dense metallic
spectrum. White noise can also work when the filter and envelope provide enough
shape.

## Filter

A high band-pass region with moderate-to-high resonance emphasizes the metallic
character. Compared with a hi-hat, the cymbal often benefits from a more
focused resonant band and a lower overall level.

## Envelope and movement

The decay is substantially longer than a closed or open hat. A strongly
exponential slope keeps the attack clear while letting the tail dissolve.
Slow filter movement can make successive strikes differ slightly in spectrum,
which prevents a repeated cymbal from sounding static.

## Design alternatives

Crash-like accent:
    dense metallic source + bright band-pass + long decay

Ride-like texture:
    metallic source + resonant band-pass + slow filter movement

## What NOT to assume

Do not reuse hi-hat decay and filter settings unchanged. The longer tail and
lower mix level are central to keeping a cymbal from masking the groove.

## Musical references

These point to the music-theory layer for decisions *around* this voice
(pattern, pitch material, role in the arrangement and mix). They do not
cover synthesis; the sections above stay authoritative for the DSP.

- `.claude/skills/music-theory/references/instrument-idiom/drums-percussion.md` — "Fill design" and "Density arc", for crashes marking section changes vs. ride-like continuous motion
- `.claude/skills/music-theory/references/orchestration/arrangement-density.md` — "The arc of density across a piece" and "EDM density arc", for when a cymbal adds energy
- `.claude/skills/music-theory/references/production-aware/energy-and-dynamics.md` — "Sectional energy mapping" and "EDM build automations", for transition use
