# Bell

## Sonic function

A bell is a pitched but spectrally complex percussion voice. Its identity comes
from inharmonic partials, a clear onset, and an exponential decay that lets the
metallic resonance ring out.

## Minimal architecture

trigger
→ FM or detuned oscillator network, or an impulse into a resonator bank
→ optional band-pass filter
→ exponential amplitude envelope (the resonators supply their own)
→ output

Optional:
→ transient generator
→ sample-rate reduction

## Partial structure

A struck bell's partials are not a harmonic series. The church-bell names, relative to the prime (the pitch the ear names), are hum 0.5, prime 1, tierce 1.2 (a minor third), quint 1.5, nominal 2, then upper partials near 2.5, 2.67, 3 and 4. Synth Secrets 40 describes three phases in the sound: an inharmonic strike that dies quickly, a strike note carried by the strong low partials, and a hum an octave below that lingers longest. Higher partials decay sooner, so the timbre darkens as the note rings. That changing balance, not one fixed spectrum, is what makes the sound read as a bell.

## FM bells

FM is useful when the carrier and modulation relationship creates a noisy,
metallic spectrum. The modulation index and frequency ratio should be treated
as interacting controls: increasing index can make the sound brighter, more
metallic, or harsher depending on register and ratio.

Chowning's bell uses a non-integer harmonicity ratio (modulator = 1.4 × carrier), so the sidebands at carrier ± k × modulator fall between harmonics. It pairs that ratio with an index that falls from bright to pure over the note, and a long exponential amplitude decay. The Cycling '74 tutorial names those three ingredients as the bell. In CCRMA's tubular bell the index envelope falls faster than the amplitude (to 14% by 14% of the note, while the amplitude is still near 40%). The clang clears first and a purer ring remains, which is the same darkening the partial structure describes.

## Modal bells

A second route models the struck object directly. An impulse excites a bank of resonators, one per partial, each with its own frequency and decay time (pyo example x06/03 excites six `ComplexRes` filters with `Metro` impulses). Unlike FM, every partial is independent:

- per-partial decay gives the darkening ring for free: scale each resonator's decay down as its ratio goes up
- strike hardness becomes the balance of the excitation across partials: a soft mallet excites mostly the low modes, and a hard one excites them all
- the partial ratios can be tuned directly. Randomising them each phrase, as x06/03 does, gives a wind chime instead of a tuned bell.

`ComplexRes` `decay` is a time constant (the time to fall by 1/e), so the time to -40 dB is about 4.6 × decay. A single-sample impulse leaves each resonator ringing at only about 1% of full scale, so the bank needs makeup gain. A resonator bank has one pitch set at a time, so retuning it while it still rings bends the tail. Give each overlapping note its own bank (rotate voices) instead.

## 808-style cowbell

A cowbell can be built from two detuned rectangle oscillators mixed together and
sent through a resonant band-pass filter. Detuning supplies the beating and
rectangular waves provide the dense, nasal spectrum.

## Envelope and filter

Use a sharp attack and a strongly exponential decay. A band-pass filter shapes
the resonance and keeps the result from spreading across the entire spectrum.

## Design alternatives

Realistic bell:
    FM network + band-pass filter + long exponential decay

Chowning FM bell (`bell.py` style `fm`):
    FM at ratio 1.4, index envelope falling faster than the amplitude envelope, long exponential decay

Modal bell (`bell.py` style `chime`):
    impulse → `ComplexRes` bank at church-bell ratios, per-partial decay, strike tilting the excitation

Wind chime, not implemented yet:
    `Metro` impulses at several unrelated rates → `ComplexRes` bank at random frequencies, retuned every phrase (x06/03 as written)

808-style cowbell:
    two detuned rectangle oscillators + resonant band-pass

## What NOT to assume

Metallic complexity does not come from FM index alone. Carrier frequency, ratio,
filtering, decay, and output level all affect whether the result reads as a
bell, clang, zap, or noisy accent.

Increasing:

- strike → brighter, more clanging onset; in FM the peak index, in the modal bank the weight of the upper partials
- ring → longer notes; with a short phrase grid they overlap into a wash

## Musical references

These point to the music-theory layer for decisions *around* this voice
(pattern, pitch material, role in the arrangement and mix). They do not
cover synthesis; the sections above stay authoritative for the DSP.

- `.claude/skills/music-theory/assets/modes-cheatsheet.md` and `intervals-and-scale-formulas.md` (same folder) — for choosing bell pitches or a pattern's pitch set
- `.claude/skills/music-theory/references/techniques/microtonal.md` — "Cents", "Just intonation" and "Indonesian gamelan", for tunings that suit inharmonic, metallic timbres
- `.claude/skills/music-theory/references/orchestration/instruments-ranges-character.md` — glockenspiel / tubular bells / crotales entries, for register and character
- `.claude/skills/music-theory/references/instrument-idiom/drums-percussion.md` — "Percussion layers", for cowbell as a groove accent

## Sources

Synth Secrets 40, "Synthesizing Bells" (Sound On Sound); the CCRMA CLM FM tutorial (tubular bell) and the Cycling '74 MSP FM tutorial (Chowning's bell); pyo examples x03/03 (FM generators), x06/03 (complex resonator) and x10/01 (break-point envelopes), pyo 1.0.6 documentation. The church-bell partial ratios are the standard campanology values (as in Rossing, *The Science of Sound*), quoted from memory and not re-checked against a fetched source.
