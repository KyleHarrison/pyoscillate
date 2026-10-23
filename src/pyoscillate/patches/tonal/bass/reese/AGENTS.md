# Reese bass

## Sonic function

A Reese bass is a sustained low line made from several slightly detuned saws. Their beating produces a slow phasing, hollow-then-full movement that is the whole identity of the sound; the notes are often long and few.

The family also covers the **wobble**: the same detuned stack with a tempo-locked LFO moving a resonant low-pass, so the bass opens and closes in time with the drums. Dubstep is built on it. Wobble speed is a fraction of the bar (1/2, 1/4, 1/8, the triplets, 1/16), never a free Hz value, so it stays in time at any BPM.

## Minimal architecture

trigger/gate
→ 2–3 saws (or a `SuperSaw` stack), slightly detuned
→ low-pass, static or swept by a bar-fraction LFO restarted on every note
→ optional waveshaping after the filter (the resonance peak feeds it: the growl)
→ amplitude envelope held for the note's length
+ a sine sub at the note's pitch, outside the filter and the shaper

## Design alternatives

Tempo-locked wobble (`reese.py`):
    `SuperSaw` → `MoogLP` with cutoff `Brightness × 2^lfo` → `Disto`; a sine LFO restarted on each note, started at its minimum so every note opens from a closed filter; a clean sine sub beside it. Styles `wobble` (eighths, held roots and stabs) and `heave` (half notes, one held root a bar).

Static Reese, not implemented yet:
    the same stack with a fixed or very slowly moving cutoff and long sustained notes; the beating alone is the movement.

## Boundaries

A Reese is still a gated bassline. If the detuned stack holds one pitch and never re-articulates, it is a drone (`tonal/drone`), not a Reese.

## What NOT to assume

- A deeper wobble is not "more bass": it moves energy between the filter's closed and open states, so a wide wobble can leave the low end thinner at its peak. The sub sits outside the filter so the weight stays steady.
- Pyo's `MoogLP` can blow up to NaN with a hot input and a fast, wide sweep, which the limiter turns into silence. Trim the stack before the filter and cap the cutoff well under Nyquist.

## Musical references

These point to the music-theory layer for decisions *around* this voice
(pattern, pitch material, role in the arrangement and mix). They do not
cover synthesis; the sections above stay authoritative for the DSP.

- `.claude/skills/music-theory/references/electronic-parts/bass-lines.md` — register and kick interaction
- `.claude/skills/music-theory/references/techniques/microtonal.md` — "Cents", for reasoning about detune and beating rate
- `.claude/skills/music-theory/references/genres/electronic-edm.md` — dubstep (half-time, wobble as the primary content) and DnB / jungle context
