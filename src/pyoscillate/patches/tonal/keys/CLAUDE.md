# Keys

## Sonic function

Keys are a gated, polyphonic chordal voice with a struck attack and a bell-like decay, in the electric-piano family. Velocity changes brightness as well as level: a hard strike "barks", a soft one is round.

## Minimal architecture

trigger (velocity)
→ tine/tone source (FM or additive)
→ attack transient (bark) scaled by velocity
→ decaying amplitude envelope (no true sustain)
→ optional tremolo / chorus

## The instrument being modelled

In a Rhodes, a hammer strikes a thin tine attached to a larger tone bar. The pair acts as a tuning fork: the tone bar reinforces and extends the tine's vibration, and a pickup opposite the tine turns it into signal. Moving the tine and pickup closer gives the characteristic bell-like sound. The Rhodes sustains longer and is mellower; the Wurlitzer, a reed instrument, produces strong harmonics when played hard and has more "bite". The Suitcase Rhodes' built-in amplifier adds a tremolo that bounces the sound between two speakers (Wikipedia, "Rhodes piano").

So there are three separate parts to model:

- a **body**: a nearly sinusoidal tone at the note's pitch, which decays slowly and gets purer as it rings
- a **tine ping**: a short, bright, inharmonic burst at the strike, which grows much louder with harder playing
- **no sustain**: once struck, the note only decays

## FM electric piano

FM became the standard electric-piano synthesis on the DX7, whose E.PIANO patches pair two operator stacks on the same pitch:

- the **body** stack is carrier and modulator at ratio 1, with a low index. That gives a few harmonics above a sine: round at index 0, reedy and Wurlitzer-like as it rises.
- the **tine** stack puts a 14:1 modulator on the carrier. Its sidebands sit around the 13th to 15th harmonic, far above the body. The modulator's envelope dies inside a tenth of a second, and velocity drives it, so playing harder opens the timbre instead of only raising the level (search summary of DX7 E.PIANO analyses).

pyo example x10/01 builds one FM note from three break-point tables (amplitude, ratio, index) and reads each at 1/dur, so the same shapes fit any note length. `keys.py` uses the amplitude and index tables that way, with `TrigEnv` `dur` as the reader duration. It leaves out x10/01's ratio table: a ratio that moves mid-note retunes the sidebands, which sounds like a synth sweep rather than a struck instrument. The tine's second, fixed high ratio takes that role instead.

- **Velocity shapes the tine more than the level.** `keys.py` scales the tine index by velocity squared and the body index by half to full velocity. Soft notes lose the ping entirely but keep some of the body.
- **The tine pair needs its own, short amplitude envelope.** pyo's `FM` integrates frequency, so the tine's index burst leaves its carrier out of phase with the body's carrier on the same pitch. A tine carrier left ringing partly cancels the body's fundamental, so a hard note ends quieter than a soft one. Fading the tine pair within a few hundred milliseconds, as a DX7's tine stack does, leaves only the body ringing.
- **Ratio 1 puts a sideband on 0 Hz.** The body's first lower sideband is DC, and it follows the index envelope. A subsonic high-pass below the lowest note removes it (the FM bass has the same issue).
- **The index falls faster than the level**, as in the bells (`pitched_percussion/bell`). The chord mellows as it rings.
- **Close voicings suit keys.** Rootless ninth voicings keep four notes inside an octave. A comping rhythm (the Charleston: beat one, then the "and" of two) gives the struck attack something to articulate.

Increasing:

- bark → a brighter, glassier ping on hard notes; soft notes change much less
- bite → the sustained tone moves from mellow and Rhodes-like to reedy and Wurlitzer-like
- decay → from short stabs to chords that ring into each other
- tremolo → the level throbs in 8th notes

## Design alternatives

FM tine piano (`keys.py`):
    per note: body FM (ratio 1, falling index, exponential decay over Decay) + tine FM (ratio 14, index dying in 80 ms × velocity², its own 0.3 s decay at half level), subsonic high-pass, 8th-note tremolo

Stereo suitcase tremolo, not implemented yet:
    pan the voice between channels with the tremolo LFO instead of modulating its level

Ratio-envelope FM keys, not implemented yet:
    x10/01 as written: the ratio steps between 0.5, 0.25 and 1 over the note, for a stranger, synthetic keyboard rather than an electric piano

Additive tine, not implemented yet:
    a sine body plus a few short, inharmonic sine partials for the strike, as the bell's modal route does

## Boundaries

Unlike `pad/`, keys articulate every chord with a percussive attack and decay; unlike `pitched_percussion/bell`, the partials are close to harmonic so chords stay clear. The 14:1 tine is an integer ratio, so its sidebands land on harmonics too; they are just so high and brief that the ear hears a ping rather than a pitch, and the chord it leaves behind is plain and clear.

## What NOT to assume

- Bark is not brightness in general. It only adds a ping on the front of the note, and mostly on hard notes. A brighter sustained tone is Bite.
- Louder is not harder. Velocity changes the tine far more than the level, so an accent that only raises the level sounds like a turned-up soft note.

## Musical references

These point to the music-theory layer for decisions *around* this voice
(pattern, pitch material, role in the arrangement and mix). They do not
cover synthesis; the sections above stay authoritative for the DSP.

- `.claude/skills/music-theory/references/instrument-idiom/piano-keyboards.md` — voicing rules and comping
- `.claude/skills/music-theory/references/electronic-parts/chords-and-voicing.md` — "Keys and stabs — close voicing is fine"

## Sources

Wikipedia, "Rhodes piano" (tine, tone bar, pickup, Wurlitzer bite, Suitcase tremolo); DX7 E.PIANO analyses as summarised by a web search (the 14:1 tine modulator dying inside a tenth of a second, velocity driving it). That is a secondary summary: check it against the DX7 ROM patch data before relying on the exact numbers. Also pyo example x10/01 (break-point envelopes), pyo 1.0.6 documentation.
