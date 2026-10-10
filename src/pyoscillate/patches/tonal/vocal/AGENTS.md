# Vocal

## Sonic function

A vocal voice is a held, pitched voice that sounds like a person singing or whistling: a note starts, is held as long as the phrase says, and lets go. Unlike `tonal/lead` it is shaped by a mouth rather than a filter, so what makes it a voice is not its pitch but the *vowel* the pitch is sung on. Unlike `tonal/pad` the notes follow a phrase on the clock; unlike `tonal/strings` the ensemble is people, each a little out of tune and out of step with the rest.

## Minimal architecture

gate (a held note, `common.Held`)
→ pitch: glide, vibrato that blooms in after the note starts, a slow random wander
→ source: a buzz at the pitch (the vocal folds) or a near-pure tone (a whistle)
→ breath: noise let in beside the source
→ tract: five formant filters (a voice) or one sharp resonance (a whistle)
→ note envelope (attack, release)
→ room (reverb)

## Formant synthesis

A voice is a source and a filter. The vocal folds buzz at the pitch, a harmonically rich wave that falls away about 12 dB an octave; the throat and mouth then boost the harmonics that fall near their resonances, the formants. A vowel is the position of the first two or three of them: 'oo' has its first formant low and its second low, 'ee' has the second very high. The pitch is the source's, the vowel is the filter's, and they do not depend on each other, which is why a low-pass filter on a sawtooth is a synth and not a voice.

- **The source** is a band-limited sawtooth, rolled off by Brightness (how hard the voice is pushed). It is not a model of a glottal pulse, only of its spectral tilt.
- **The tract** is `FormantSinger`: five `Reson` band-pass filters in parallel, each at a formant frequency, a bandwidth and a level taken from a table (`VocalTract`: soprano, alto, tenor and bass, the classic singing-voice formant data as tabulated in the Csound manual, five vowels each). A small share of the unfiltered buzz is let past (`direct_mix`), since a real mouth passes a little of everything and a note that falls between two formants should be quieter, not gone.
- **Vowel** runs through the five vowels in the order a vowel triangle runs (`oo oh ah eh ee`), so neighbours are acoustically close and the table is interpolated between them: a sweep is a smooth 'wah' or 'yeah'. Every formant moves through its own `SigTo`, so a swept or sudden change glides.
- **Throat** divides every formant frequency: a larger throat is deeper and more hollow, a smaller one is a child's or a cartoon's, with the pitch untouched. **Focus** sharpens or softens every formant; a sharper formant passes less of the buzz, so each is brought back up by Focus to the power `focus_makeup`, which holds the loudness (measured, see the test findings).
- **Breath** is noise let into the tract beside the buzz, so a breathy voice is shaped by the same vowel, not a hiss laid on top of it.

## Held notes

`common.Held` (see [patches/AGENTS.md](../../AGENTS.md)) owns everything about *when* and *at what pitch*, and `Singer` adds what a voice has: Breath, an Unsteadiness that wanders the pitch (slow random, a voice's own drift, which an ensemble gives every singer separately), and a room (`Reverb`). Vibrato is the singer's most characteristic motion: it is not there at the start of a note but grows in (Vibrato bloom), which is why a held note sounds sung rather than sampled. Legato is how far a note is held toward the next; a slur at full Legato, a gap below it.

A line voice (the solo voices, the whistle) plays one chord tone at a time from a hook or lead phrase. A chord voice (the choir, the angels) plays every tone of a chord shape on a chord rhythm, one voice per tone. The unused voices of a chord voice are silenced by `voice_gain`.

## Ensembles

A section is not one voice louder. `Ensemble` repeats every note in `copies` detuned copies, spread either side of the pitch by Spread (cents), each with its own vibrato speed (`vibrato_scatter`) and its own drift, so the section shimmers and moves instead of beating on one fixed interval. The voices add in power, so each is trimmed by one over the square root of the section's size (`section_trim`): a choir of ten is about as loud as a soloist.

## Whistling

A whistle is air over the lips with the mouth's cavity ringing at the pitch, so what is heard is almost a sine with a narrow band of hiss around it. `Whistling` is a `Singer` without formants: a sine at the pitch (Edge adds a faint second harmonic for a harder, shriller whistle) plus the breath noise through a very sharp resonator tuned to the same pitch (Purity is how sharp), and a low-pass (Brightness).

## Design alternatives

Formant voice (`solo.py`, `ensemble.py`):
    sawtooth buzz → Brightness low-pass → five `Reson` formants + a little direct buzz → note envelope → room

Whistle (`whistling.py`):
    sine (+ Edge overtone) + breath noise through a narrow resonator at the pitch → low-pass → note envelope → room

Vowel-choice dropdown, not implemented:
    the five vowels as a catalog of named choices rather than a continuous morph, for a rack that wants 'oo' or 'ah' by name. The continuous Vowel slider already reaches them and also sweeps.

Pitch-tracking formants, not implemented:
    a soprano above her first formant raises it to follow the pitch, so high notes stay loud on every vowel. Here the formants are fixed, so a note above the vowel's first formant is quieter (the `direct_mix` keeps it from vanishing).

Sampled or granular choir, not implemented:
    recorded vowels played back through `sample/`; truer, but not controllable in Vowel, Throat or Focus.

## Boundaries

Unlike `tonal/pad`, a vocal voice is gated by the phrase and the choir changes chord on the rack's clock; unlike `tonal/strings`, the ensemble is a few detuned, independently wobbling copies of one voice (a formant voice), not a supersaw. Unlike `tonal/lead`, the timbre is a vowel, not a filter sweep.

## What NOT to assume

- Formants are not a filter on the pitch. Raising the pitch does not move them, and moving them (Vowel, Throat) does not change the pitch.
- A larger Focus is not more of the vowel. It is a sharper, more nasal, more ringing resonance; a very high Focus on a pitch between two formants is quieter and thinner.
- The tables are the classic synthesis data, not a measurement of any singer, and the five vowels are English-like ones. Do not expect a convincing consonant or a word.
- A choir is not a chord of one voice. The ensemble is `copies` of every note; a chord with a root, third and fifth is three notes each of two or three singers.

## Musical references

These point to the music-theory layer for decisions *around* this voice
(pattern, pitch material, role in the arrangement and mix). They do not
cover synthesis; the sections above stay authoritative for the DSP.

- `.claude/skills/music-theory/references/instrument-idiom/vocals.md` — range, tessitura, vowel and breath, and where a line sits
- `.claude/skills/music-theory/references/orchestration/choral-writing.md` — SATB ranges, balance and voicing for the ensembles
- `.claude/skills/music-theory/references/electronic-parts/chords-and-voicing.md` — open voicings and voice leading for a sustained chord voice

## Sources

The formant tables are the singing-voice formant data (Dodge & Jerse, *Computer Music*) as tabulated in the Csound manual ("Formant table": soprano, alto, tenor and bass, five formants each, with frequency, level in dB and bandwidth). That is a secondary tabulation: check the figures against the original before relying on any one. The source-filter model of the voice is standard acoustic phonetics; the whistle as a resonated jet is a simplification of the same idea. pyo 1.0.5 documentation for `Reson`, `LFO`, `Randi` and `Adsr`.
