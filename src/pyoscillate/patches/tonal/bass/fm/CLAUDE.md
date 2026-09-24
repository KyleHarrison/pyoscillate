# FM bass

## Sonic function

An FM bass gets its harmonics from frequency modulation rather than filtering. The modulation index is the "growl" control: low index is round and sub-like, high index is buzzy and metallic. An index envelope makes each note bark then settle.

It is a gated bassline voice (see "Choosing a family" in `patches/CLAUDE.md`): each note is struck on the clock, and the interest is in how the brightness moves within the note, not in a filter sweep across the bar.

## Minimal architecture

trigger (accent)
→ modulator (ratio × note frequency)
    ↑ index = bark envelope × accent + steady floor
→ carrier at note frequency
→ amplitude envelope × accent
→ output

## How FM makes the spectrum

Two-operator FM puts sidebands at carrier ± k × modulator. The harmonicity ratio (modulator ÷ carrier) decides where they fall, and the index decides how many are strong (Cycling '74 MSP FM tutorial).

- **Integer ratios keep the bass harmonic.** At ratio 1 the sidebands land on every harmonic of the note, a saw-like series. At ratio 2 the lower sidebands fold back onto the odd harmonics, a hollower, square-like series. In both, the pitch stays clear at any index, which a bassline needs.
- **The index is brightness and buzz together.** Raising it pushes energy into higher harmonics, so the note gets brighter and more nasal. FM keeps the total amplitude constant whatever the index, so the level does not rise with the growl. Gain staging only has to cover the amplitude envelope and the accent.
- **Ratio 1 puts a sideband on 0 Hz.** The first lower sideband (carrier − modulator) is DC. pyo's `FM` integrates the modulated frequency, so the term does not cancel, and it follows the index envelope: every bark carries a subsonic thump that uses headroom and drags the measured brightness down. A 2nd-order high-pass below the lowest register (20 Hz) clears it. pyo's one-pole `DCBlock` is too slow for an offset that moves within milliseconds. CrossFM's feedback does the same at high index.
- **Carrier and modulator can modulate each other.** `CrossFM` feeds the carrier back into the modulator (x03/03 compares it with `FM` at the same settings). The spectrum gets denser and less predictable: grit rather than a clean bark.

## The index envelope: bark then settle

pyo example x10/01 reads the index from a break-point `LinTable` (20 → 10 in the first 512 of 8192 points, then down to 0) at reader frequency 1/dur. The same shape, normalised to 1 → 0.5 → 0 and scaled by Growl, gives each note a bright attack that falls away fast and then fades out:

- the **settle time** (the envelope's duration) is independent of the note length. A short settle is a pluck on the front of the note, and a long one is a slow close, like a filter envelope.
- `TrigEnv` outputs 0 once the table ends, so the brightness left after the bark (the **edge**) is a separate floor added to the envelope, not the table's last point.
- **Accent scales the bark as well as the level.** Brass-like FM ties brightness to loudness (the Cycling '74 trumpet tracks the index to the amplitude). A bassline's accents then hit brighter as well as louder, which is what makes an FM groove feel played rather than stamped.

Increasing:

- growl → a brighter, more snarling attack on every note
- settle → the bark lingers into the note, from a click-like pluck to a wah
- edge → a buzz that stays under the whole note, instead of settling to a pure sub
- length → notes run into each other instead of being staccato

## Design alternatives

Clean FM bark (`fm.py` style `bark`):
    FM at ratio 1, index = bark envelope + edge floor, accent on both index and level, subsonic high-pass

Gritty cross-FM (`fm.py` style `grit`):
    CrossFM at ratio 2, the carrier feeding back into the modulator at half the main index

Index envelope from a CrossFM table, not implemented yet:
    the `CrossFM` docstring example uses `LinTable([(0,20), (200,5), (1000,2), (8191,1)])`, a slower settle to a non-zero floor, for a bell-bass hybrid

## Boundaries

Integer ratios keep the bass harmonic and tonal; non-integer ratios drift toward the bell family (`pitched_percussion/bell`) and lose pitch clarity in the low register.

A resonant filter sweep with slide and accent is `tonal/bass/acid`. A detuned-saw beating bass is `tonal/bass/reese`. A continuous FM sub bed with no note line is a drone (`tonal/drone`).

## What NOT to assume

- More index is not always "more bass". It moves energy away from the fundamental, so a high growl can sound thinner under a kick even as it gets brighter.
- The ratio is not a tone control. Changing it changes which harmonics exist, and a non-integer value changes whether the note has a pitch at all.

## Musical references

These point to the music-theory layer for decisions *around* this voice
(pattern, pitch material, role in the arrangement and mix). They do not
cover synthesis; the sections above stay authoritative for the DSP.

- `.claude/skills/music-theory/references/electronic-parts/bass-lines.md` — movement and kick interaction
- `.claude/skills/music-theory/references/instrument-idiom/bass.md` — synth bass role

## Sources

Cycling '74 MSP FM tutorial (harmonicity ratio, index, sidebands, the brass index envelope); pyo examples x03/03 (FM generators) and x10/01 (break-point envelopes), and the `CrossFM` docstring, pyo 1.0.6 documentation.
