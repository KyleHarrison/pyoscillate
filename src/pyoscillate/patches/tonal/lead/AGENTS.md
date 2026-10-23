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

## FM leads

Two-operator FM gets its colour from the modulator/carrier ratio and the index, not from a filter. An integer ratio keeps the tone harmonic (ratio 2 folds the sidebands onto the odd harmonics: hollow and reed-like); a ratio a little off an integer (3.01) puts the sidebands slightly off the harmonics so they beat against them, which reads as phasing or shimmer. The index is the "bite": an envelope that barks on each note and settles to a steady edge gives an articulate attack, and a slow LFO on the index keeps the colour moving between notes.

For a windy, breathy character, add band-passed noise that tracks the note pitch (breath), a slow multiplicative pitch drift, portamento between notes, and a tempo-synced echo. Keep breath and echo as separate nodes from the gated amplitude envelope: writing `.mul` on a product that carries the envelope replaces the envelope with a constant.

Band-passed noise has a much higher crest factor than a sine, so a breath layer that sounds level with the tone has about three times its peak; leave headroom for that in the default volume.

FM leads live in `fm.py`; the pulse-subtractive leads in `lead.py` are a different topology and do not share its graph.

## Subtractive synth leads

`synth.py` holds `SynthLead`, a `Lead` whose two oscillators are chosen per style (saw, square or triangle, each its own pitch offset and level) and the six lead recipes of the cookbook as its styles: Mono Solo, New Age Lead, R&B Slide, Screaming Sync, Strings PWM and Trance 5th. The graph, controls and played line are `Lead`'s; only `make_source()` differs.

- A square is a true pulse (a sawtooth minus itself delayed by the pulse width, `pad.pad.Wave`): `lead.py`'s pulse is pyo's type-4 `LFO`, which is no duty-cycle square.
- The pulse width sways on a slow LFO shared by both oscillators (the recipes' "PW osc1, osc2").
- Screaming Sync hard-syncs the second oscillator to a silent first (read from a table at the master's phase times the pitch ratio) and swings its pitch on a slow LFO.
- Filter cutoffs are the cookbook's knob positions in Hz (20 Hz to 20 kHz on a log scale, kept under 10 kHz where `MoogLP` is stable); the envelope's travel is the Brightness slider.

Left out: the recipes' unison voices and the string chorus and delay.

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
