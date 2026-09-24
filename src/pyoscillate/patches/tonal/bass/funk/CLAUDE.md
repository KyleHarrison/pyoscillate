# Funk bass

## Sonic function

A funk bass is a gated, syncopated low line with a vocal "quack" on every note. The quack is a resonant low-pass opened by a per-note envelope with a slow attack, so the filter swells open *across* the note instead of clicking open at its start. The line's space, ghost notes and octave pops carry the groove; the filter sweep makes it talk.

It is a gated bassline voice (see "Choosing a family" in `patches/CLAUDE.md`): each note has a gate, and the envelopes sustain for the gate's length and release when it closes.

## Minimal architecture

gate (accent, length) + pitch with a short glide
→ saw (osc 1) + narrow pulse an octave up (osc 2), equal level
→ 24 dB resonant low-pass, almost closed at rest
    ↑ filter ADSR, slow attack, counted in octaves above the resting cutoff; accent deepens it
→ amplitude ADSR, instant attack, sustains lower; accent scales it
→ output

## The recipe

From Welsh's Synthesizer Cookbook, "Funk Bass":

| Section | Setting |
| --- | --- |
| Osc 1 | saw, −2 oct, 0 dB |
| Osc 2 | pulse, width 30%, −1 oct, 0 dB, key tracking on, no sync |
| Noise, LFO, unison | off |
| Voice | mono, glide on, 0.02 s |
| Low-pass | 24 dB, cutoff 40 Hz (10%), resonance 50%, envelope amount 85% |
| Filter ADSR | 0.15 s, 0.10 s, 45%, 0.08 s |
| Amp ADSR | 0 s, 0.29 s, 30%, 0.40 s |

Reading it:

- **The slow filter attack is the sound.** 150 ms is longer than a 16th at most tempos. Held notes reach the top of the sweep and quack; short ghost notes end before the filter opens, so they stay dark and percussive. This is why a funk line's ghosts sound "dead" without any separate muting.
- **The resting cutoff is below the fundamental.** At 40 Hz the filter mostly passes nothing on its own. The envelope does the work, so the envelope amount matters more than the cutoff.
- **Map the envelope exponentially.** The cookbook's percentages are knob positions on an analogue synth whose envelope drives the cutoff in volts per octave. An exponential mapping (octaves above the resting cutoff) quacks bright and settles dark. A linear mapping in Hz keeps the sustain bright, which sounds like a static filter, not a quack.
- **Osc 2 an octave above osc 1** puts the pulse's nasal, hollow edge over the saw's body. Since both play the same note, the pair still reads as one pitch.
- **The amp decays to 30% while the filter is still opening.** The note's loudest moment and its brightest moment are 150 ms apart, which gives the "wow" its shape.

Increasing:

- quack → a wider sweep; accented notes talk more, ghosts barely change
- swell → a lazier wah that only held notes complete; decreasing it is a plucky, clicky filter snap that also brightens ghosts
- brightness → a buzzier edge on every note, including ghosts
- growl → a more rubbery, nasal peak riding the sweep
- length → notes hold into the space; shorter leaves more gap in the groove

## pyo notes

- **`MoogLP` blows up with a hot input.** Swept fast to several kHz, it turns to NaN once its input peaks well above 1, and the patch limiter then silences the patch for good. Trim the oscillator mix to about 1 before the filter and cap the cutoff well below Nyquist.
- **`Adsr` with `dur` won't release mid-decay.** It finishes the decay, then drops straight down, which clicks. For gates shorter than attack + decay, run the envelope with `dur=0` and call `stop()` at note-off. `stop()` releases from wherever the envelope is.
- **A pulse from one saw table:** a saw minus the same saw shifted by the pulse width is a zero-mean, band-limited pulse of that width. pyo's `LFO` `sharp` parameter is not a pulse width.

## Design alternatives

Cookbook funk (`funk.py`):
    saw + 30% pulse, 24 dB ladder, exponential filter ADSR with slow attack, amp ADSR, 20 ms glide, a syncopated minor-seventh line with ghosts and octave pops

Envelope-follower auto-wah, not implemented yet:
    a plainer bass voice into a band-pass or low-pass whose cutoff follows the input level, the "Mu-Tron" pedal version; the quack then follows how hard the note is played, not a per-note envelope

## Boundaries

A fast filter envelope with slide and accent on a driving 16th-note pattern is `tonal/bass/acid`. The topology is close (per-note filter envelope, glide), and when acid is implemented the voice here is the place to lift a shared builder from. The difference is the phrasing and envelope timing, not the graph: acid's filter decays fast and its accent shortens it; funk's filter attacks slowly.

A fixed-cutoff groove bassline is the shared `tonal/bass` core.

## What NOT to assume

- More resonance is not more bass. The ladder filter thins the low end as resonance rises, so a higher Growl sounds quieter and more nasal under the kick.
- The cookbook's percentages are not portable numbers. They describe knob positions; the octave depth here was chosen by ear and measurement.

## Musical references

These point to the music-theory layer for decisions *around* this voice
(pattern, pitch material, role in the arrangement and mix). They do not
cover synthesis; the sections above stay authoritative for the DSP.

- `.claude/skills/music-theory/references/instrument-idiom/bass.md` — "Funk/R&B": syncopated riff, ghost-note feel, space as groove; "Bass fills kick gaps"
- `.claude/skills/music-theory/references/rhythm-groove/groove-and-feel.md` — syncopation and ghost notes

## Sources

Welsh's Synthesizer Cookbook, "Funk Bass" patch sheet; pyo 1.0.6 documentation for `MoogLP`, `Adsr` and `TrigEnv` (its end-of-envelope `trig` stream).
