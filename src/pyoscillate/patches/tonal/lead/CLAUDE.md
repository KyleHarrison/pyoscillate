# Lead

## Sonic function

A lead is the primary monophonic melodic voice. It communicates pitch, phrase, and motion directly, so its design priorities are clarity, articulation, and expressive control rather than long sustain for its own sake.

## Minimal architecture

oscillator(s)
→ harmonic shaping
→ amplitude envelope
→ optional filter contour
→ optional vibrato or pitch modulation
→ optional stereo or spatial treatment

## Key design traits

- monophonic or quasi-monophonic focus
- brighter spectral profile than a bass or pad
- direct attack and controlled release
- optional vibrato, portamento, or subtle pitch drift
- harmonic richness can vary from clean and focused to aggressive and saturated

A lead should be heard as a voice that carries the melody, not as a general-purpose background tone.

## Parameter logic

The most important controls are usually:

- brightness: more or less harmonic presence
- attack: sharper or softer articulation
- sustain: more or less body in the phrase
- vibrato: motion and expressiveness
- drive or saturation: more aggression, compression of the voice

## Design alternatives

Clean lead:
    simple oscillator + moderate attack + stable filter

Expressive lead:
    slightly detuned oscillators + vibrato + short portamento

Aggressive lead:
    more harmonics + drive + stronger envelope shaping

## What NOT to assume

A lead should not be treated as a generic oscillator patch. It must be judged by how clearly it carries the melodic role: whether it remains intelligible, articulate, and expressive in context.

## Musical references

These point to the music-theory layer for decisions *around* this voice
(pattern, pitch material, role in the arrangement and mix). They do not
cover synthesis; the sections above stay authoritative for the DSP.

- `.claude/skills/music-theory/references/melody/melodic-construction.md` — contour, range, steps vs. leaps and chord-tone placement, i.e. what the lead has to carry clearly
- `.claude/skills/music-theory/references/melody/phrase-structure.md` and `motivic-development.md` (same folder) — for phrase length and motif repetition in sequenced lines
- `.claude/skills/music-theory/assets/modes-cheatsheet.md` and `intervals-and-scale-formulas.md` (same folder) — for scale/mode choice
- `.claude/skills/music-theory/references/production-aware/arrangement-for-mix.md` — "The mid-range problem", for choosing register and brightness so the lead stays readable
