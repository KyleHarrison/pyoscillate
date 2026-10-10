# Keys

## Sonic function

Keys are a gated, polyphonic voice played from a keyboard: it plays the rack's chords, as a chord struck on a rhythm, or a figure of its tones. There are three kinds, which differ in what happens after the key goes down:

- **Struck and ringing** (`keys.py`, `celeste.py`): a bell-like decay with no sustain, in the electric-piano family. Velocity changes brightness as well as level: a hard strike "barks", a soft one is round.
- **Strings** (`string_keys.py`: piano, harpsichord, clavichord): a string is set going and rings down. What sets it going is the instrument.
- **Held** (`sustained.py`, `organ.py`, `accordion.py`): the note sounds for as long as the key is down and lets go over a release, so it is a held voice (`common.Held`), not a struck one.

The sections below start with the electric piano, and then cover each of the others.

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

## Celeste

A celesta strikes steel bars with soft hammers over wooden resonators. The bars are thin, so the sound is almost a pure sine with a faint, glassy ping, and it rings for seconds. `celeste.py` is the electric piano's FM struck keyboard (`FmKeys`, the shared base in `keys.py`) with the body kept nearly sinusoidal (low Bite), the tine moved to a lower, non-integer ratio (5.4, a bar's overtone is not a harmonic, so the ping shimmers a little off the pitch), a longer, quieter ping (0.12 s of index, 0.6 s of level) and a slow, high quarter-note pulse, so each chord is heard. Bark, Bite and Decay keep their electric-piano meaning, with the Celeste's own help text.

## Keyboards with strings

A piano, a harpsichord and a clavichord each set a string going and let it ring; they are the plucked-string family's Karplus-Strong string (`pluck/string.py`, a noise burst into a tuned `Waveguide`, so each note starts bright and mellows as it rings) with an instrument's strings and its soundboard. `KeyedString` in `string_keys.py` is the shared base (`PluckedString` with `Courses` for the strings of a note and `Body` for the soundboard). It adds a chord strike: a chord rhythm strikes every tone of `chord_shape` at once through the string bank, which has room for a chord to ring over the next one; a figure strikes one note at a time. The instruments differ in what sets the string going and what follows:

- **Piano**: a felt hammer (Hardness) strikes three unison strings a little out of tune with each other, so a note beats and sings (Spread, Strings struck); the soundboard is broad and low; the sustain pedal lifts the dampers and every other string rings in answer (Pedal, the `Sympathy` mixin tuned to the chord's root, fifth and octave); a felt strip between hammers and strings is the Mute pedal.
- **Harpsichord**: a quill plucks with the same force whatever the touch (Dynamics is 0 by default, and the help text says why), a hard, dry, bright pluck near the end of the string; two unison ranks and a rank an octave above are drawn together (Registers, Spread); a strip of leather is the buff stop (Mute); the jack's click and return are the Jack click.
- **Clavichord**: a brass tangent strikes and stays on the string, damped by cloth, so it is the quietest and most touch-sensitive (Dynamics 0.9); the player can rock the tangent for a tiny vibrato that only a clavichord has (Bebung, the string's Vibrato); paired strings in unison; a small box.

`PluckedString` has no note-off and no inharmonicity. A real piano string is stiff, so its upper partials are sharp of harmonic, which gives its brightness and its piano-ness at the extremes; this one is perfectly harmonic. A key lifted does not damp its string; the string rings for Sustain. Treat each as the voice of the instrument, not a model of its mechanism.

## Held keyboards: organ and accordion

An organ or an accordion sounds for as long as its key is down, so these are `common.Held` voices, and what they add is a stack of **ranks**: `RankedKeys` in `sustained.py`. A rank is one oscillator per sounding note at a fixed ratio to its pitch, with its own level; the instrument's tone is the balance of its ranks. A style lists its `ranks` (ratios), builds one rank's oscillator in `rank_tone()`, and declares a `Param` for each rank it wants a control for. The ranks are trimmed by the square root of their total (`apply_ranks`), so a full set is louder than one rank, but not as many times louder as it has ranks.

- **Organ**: nine sine ranks on the harmonic series, the drawbars: 16' an octave below, 5⅓', 8' the note, 4', 2⅔', 2', 1⅗', 1⅓' and 1'. Each is set in the organ's own steps, 0 (off) to 8, each 3 dB. A few low bars is a round, sweet flute; all of them is a piercing chorus. Percussion adds a second or third harmonic that dies away on every key press (a pluck on a steady tone), the key click is the tick of the contacts, the Leslie speaker is a swinging delay (a Doppler pitch bend) and a pulsing level at the rotor's speed, which takes a second to speed up, and the tube preamp saturates it all (Drive, rescaled so a held chord keeps its loudness).
- **Accordion**: free reeds, a buzzing sawtooth whose sharpness is Reed edge, in four ranks: bassoon 16', clarinet 8', a second 8' tuned the other way (the musette, whose beating is the instrument's wet shimmer; Musette tuning is the whole width of it) and piccolo 4'. The reed chamber rolls off the top (Brightness), the bellows shake is a fast tremolo of the level (Bellows shake, Shake speed) and a puff of air chiffs on the front of the note. Attack is how quickly the bellows get a reed speaking.

Both play a chord on a chord rhythm and a figure of chord tones on a hook or lead phrase.

An organ's drawbar sines are not pipes (no wind noise, no chiff, no detuned pipe sets), and its Leslie is a delay and a tremolo, not a horn and a drum with their own speeds and crossover. An accordion's sawtooth is a rich wave through a low-pass, not a reed's real tone, and there is no bellows reversal or pressure-dependent pitch.

## Design alternatives

FM tine piano (`keys.py`):
    per note: body FM (ratio 1, falling index, exponential decay over Decay) + tine FM (ratio 14, index dying in 80 ms × velocity², its own 0.3 s decay at half level), subsonic high-pass, 8th-note tremolo

Stereo suitcase tremolo, not implemented yet:
    pan the voice between channels with the tremolo LFO instead of modulating its level

Ratio-envelope FM keys, not implemented yet:
    x10/01 as written: the ratio steps between 0.5, 0.25 and 1 over the note, for a stranger, synthetic keyboard rather than an electric piano

Additive tine, not implemented yet:
    a sine body plus a few short, inharmonic sine partials for the strike, as the bell's modal route does

Celeste (`celeste.py`):
    the same FM pair with a near-sine body, a 5.4:1 tine and a longer, quieter ping

Piano, harpsichord, clavichord (`string_keys.py`):
    a Karplus-Strong string bank with strings (`Courses`) and a soundboard (`Body`); the piano adds `Sympathy` as its pedal

Organ (`organ.py`), accordion (`accordion.py`):
    a `Held` voice with a bank of ranks (sine drawbars; reed sawtooths), then percussion/key click/Leslie/preamble (organ) or chamber/shake/chiff (accordion)

Stiff-string piano, not implemented yet:
    an all-pass chain in the string's loop to make the upper partials sharp, for a piano's real inharmonicity

Sampled keys, not implemented yet:
    recorded notes played back through `sample/`; truer, but not controllable in a hammer, a quill or a drawbar

## Boundaries

Unlike `pad/`, the struck keys articulate every chord with a percussive attack and decay (the held keys, the organ and the accordion, are closer to a pad: they sustain a chord and re-articulate it on the clock, and differ in that a phrase decides how long each note is held); unlike `pitched_percussion/bell`, the partials are close to harmonic so chords stay clear. The 14:1 tine is an integer ratio, so its sidebands land on harmonics too; they are just so high and brief that the ear hears a ping rather than a pitch, and the chord it leaves behind is plain and clear.

## What NOT to assume

- A string keyboard is not a hook patch. It plays chords as well: set the phrase to a chord rhythm and every tone of the chord is struck at once.
- Dynamics is not an expressive nicety on every keyboard. A harpsichord has none, a clavichord has the most, and the defaults say so.
- A held keyboard's Legato is how long the key is down, not how long the sound lasts. Release is what rings after.

- Bark is not brightness in general. It only adds a ping on the front of the note, and mostly on hard notes. A brighter sustained tone is Bite.
- Louder is not harder. Velocity changes the tine far more than the level, so an accent that only raises the level sounds like a turned-up soft note.

## Musical references

These point to the music-theory layer for decisions *around* this voice
(pattern, pitch material, role in the arrangement and mix). They do not
cover synthesis; the sections above stay authoritative for the DSP.

- `.claude/skills/music-theory/references/instrument-idiom/piano-keyboards.md` — voicing rules and comping; the registers and idioms of the piano, harpsichord, organ and the others
- `.claude/skills/music-theory/references/electronic-parts/chords-and-voicing.md` — "Keys and stabs — close voicing is fine"

## Sources

Wikipedia, "Rhodes piano" (tine, tone bar, pickup, Wurlitzer bite, Suitcase tremolo); DX7 E.PIANO analyses as summarised by a web search (the 14:1 tine modulator dying inside a tenth of a second, velocity driving it). That is a secondary summary: check it against the DX7 ROM patch data before relying on the exact numbers. Also pyo example x10/01 (break-point envelopes), pyo 1.0.6 documentation. The drawbar footages and the Hammond-style percussion and key click, the Leslie speaker's Doppler and tremolo, the accordion's reed ranks and musette tuning, and the harpsichord's quill and registers are well-established instrument facts, written here from general knowledge and not re-checked against a fetched source.
