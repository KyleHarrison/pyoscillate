# Woodwind

## Sonic function

A woodwind is a held, pitched voice that sounds blown: a player's breath sets a pipe sounding, the note starts when the phrase says so, is held as long as the line asks and lets go. Unlike `tonal/vocal` the pipe, not a mouth, shapes the tone, so what makes it a flute or an oboe is the *source the breath excites* and the shape of the bore, not a vowel. Unlike `tonal/lead` it is shaped by breath and articulation (a tongued start, a slur, a swell) rather than a filter sweep; unlike `tonal/strings` it is a solo line, not a section. Brass (lips buzzing in a cup) is a separate family when it is built.

## Minimal architecture

gate (a held note, `common.Held`)
→ pitch: glide, vibrato that blooms in after the note starts, a slow random wander, a scoop into each fresh note
→ source: what the breath excites (a jet, a reed), supplied by the family
→ breath: noise rung by the pipe at the note's pitch, beside the source
→ pipe: a low-pass (the bore and tone holes) that opens through the note's swell and follows the pitch
→ tongue: a short noise burst on a note struck afresh
→ breath pulse: a slow tremolo of the level, grown in with the vibrato
→ note envelope (attack, release)
→ room (reverb)

## What every wind shares

`wind.py`'s `Wind` owns everything around the tone, so a family builds only its source (`make_source()`), and a style only its starting values.

- **Pipe** (Brightness, Opening, Pitch tracking): a low-pass on the whole sound, breath included. Its cutoff is Brightness, scaled by the note's own attack envelope (Opening: at 0 the pipe is as open at the first instant as at the last, at the top the note starts dull and brightens as it swells, which is the cookbook recipes' filter envelope) and by the pitch (Pitch tracking: the cutoff is multiplied by the note's pitch over A4, to a power, so a high note keeps more partials than a low one). The release closes the pipe too, so a lifted note darkens as it dies.
- **Breath and Air focus**: `Breathed`'s noise is run through a resonator at the note's pitch (`air_ratio`, a multiple of it): the hiss belongs to the note. Air focus sets how sharp the resonance is; it is level-compensated (`air_makeup`) so it changes the colour of the hiss, not its loudness.
- **Tongue and Tongue length**: a short band of noise around `tongue_ratio` times the pitch, fired by `Held.on_attack()`, which only runs for a note struck afresh. A slurred note (a note found the last one still held, at full Legato) has no consonant. The burst is added after the pipe, so Opening cannot muffle it.
- **Tremolo and Tremolo speed**: the breath's pulse, a sine on the level that grows in with the vibrato, so the first instant of a note is steady.
- **Bend**: `PitchBend`, on every fresh note only, with a range of ±3 semitones in fine steps (a wind's scoop is a fraction of a semitone, not the octave a bass takes).

The pitch comes from `Held` (Register, Attack, Release, Vibrato, Vibrato speed, Vibrato bloom, Glide, Legato, Phrase, Rate) and the drift and room from `Breathed` (Breath, Unsteadiness, Space, Tail darkness, Distance). A wind plays one note at a time from the rack's chord tones, and its default phrase is a sparse, floating line with room to breathe.

## How a pipe makes its harmonics

The family split follows the physics of the pipe, not the instrument's name (after Gordon Reid, "Synthesizing Wind Instruments", *Sound On Sound*, April 2001, in `docs/Synthesizing Wind Instruments.pdf`).

- **An open pipe has every harmonic.** Air in a pipe open at both ends rings as a standing wave whose wavelength is twice the pipe, like a string fixed at both ends: the whole series 1, 2, 3, 4... A recorder or a flute, whose edge sets the air going, is this. Overblowing jumps up an octave (C3, C4, G4, C5...).
- **A pipe closed at one end has only the odd harmonics.** A reed or the lips close the blown end, so the wavelength is four times the pipe (an octave lower than an open pipe of the same length) and the even harmonics are missing: the square wave's 1, 3, 5... A clarinet, a straight tube with a single reed, is this: hollow, and overblowing jumps a twelfth (C3, G4, E5...), not an octave.
- **A cone or a flare brings the whole series back.** A brass instrument or an oboe is also closed by a valve (lips, double reed) but its bore widens, and a cone or a flare, like an open pipe, carries every harmonic: the sawtooth's. That is why a clarinet is a square and an oboe, a bassoon, a saxophone and a trumpet are sawtooths, and why the brass family can't be a square.
- **Which harmonics exist is not enough: their levels are the timbre.** Two waveforms from the same ten harmonics sound nothing alike if their levels differ. The recorder and the trumpet both have the whole series and sound unlike each other for this reason.
- **Louder is brighter.** A quiet note on a wind is mostly its fundamental; a loud one has a dozen or more strong harmonics, and the lower ones lose share as it grows (a note blown very hard can have its eighth harmonic strongest, a squawk three octaves up). A wind's low-pass must therefore open as the note gets louder (`Opening`, driven by the note's own envelope) and, if resonance emphasises the upper harmonics, more so for a harder blow.
- **Low is richer than high.** A low note has more harmonics than a high one, because the instrument's body has less room above its top notes, so the cutoff must rise more slowly than the pitch (`Pitch tracking`).
- **Not modelled here**: the formants of the real instrument beyond the reed family's `Nasal` ring, the transient at the start of a note beyond `Tongue`, and register breaks and overblowing.

## Jet winds (`flute/flute.py`)

A flute has no reed. The breath is a jet that splits on the embouchure edge and sets the pipe's air ringing, so the tone is the pipe's own resonance: almost a sine at the pitch, a few weak overtones that fall away fast, and a band of jet noise ringing around the pitch. `JetWind` builds the source as `partials` sines at integer multiples of the pitch, each weighted by Overtones to the power of its number; the weights are normalised so Overtones changes the colour (from a pure, hollow sine to a fuller, reedier tone) and not the loudness. Flutter is the flutter tongue, a fast roll of the level (12 to 40 Hz) from full to `1 - Flutter`, present for the whole note.

`Flute` is a `JetWind` with a register of C4 to C6, a soft attack, a light blooming vibrato, a faint flat scoop and a little tongue. `flute/flute_phrases.py` holds the flute's tunes: long, fixed melodies (`FluteTunes`, written note by note as `Phrase`s) that belong to one instrument and are injected into the flute's Pattern dropdown (`FlutePhrases`: the tunes first, then every hook and lead a wind line plays). This is the one place a patch family keeps its own phrases, because a tune is a piece for one instrument; a short figure any voice could play still goes in `theory/phrase/`. `flute/piccolo.py`'s `Piccolo` is a style on the same base: an octave up, a short pipe so a nearly pure tone, a harder tongue and a sharply ringing breath. A penny whistle would be another (it lives in the cookbook's brass section).

## Reed winds (`reed/`)

`reed.py`'s `ReedWind` builds the source for every reed: `partials` sines at integer multiples of the pitch, weighted 1/n to a power set by Reed edge, with the even ones scaled by Bore. At Bore 0 only the odd harmonics sound (a cylinder, the clarinet's square); at 1 all do (a cone, the oboe's sawtooth). The weights are normalised, so neither Bore nor Reed edge changes the loudness, and both are recomputed together by `shape_partials()` (a macro: each of the two controls rebuilds the whole set from both values). `Nasal` adds a parallel resonance at a fixed frequency (`nasal_freq`, per style) ahead of the pipe, the double reed's bell and blades.

- `single.py`: `SingleReed` (a cylinder) → `Clarinet`, `ClarinetBass` (an octave lower, a little of the evens back, a slower start).
- `double.py`: `DoubleReed` (a cone, a nasal ring) → `Oboe` (bright, nasal at 1.3 kHz), `EnglishHorn` (darker, 900 Hz, a bulb bell), `Bassoon` (500 Hz, a slow breath pulse), `Contrabassoon` (an octave lower still).
- `bagpipes.py`: `Bagpipes`, a `ReedWind` (conical chanter, bright) that is never tongued and never lets go (full Legato, no Tongue, no vibrato, a long release for the bag's bleed), with a `Drone` control: odd harmonics (a reed on a cylinder) of one fixed note, `drone_ratio` of the Register, that fades in on the first note and sounds on, past the pipe, with the line. The drone is a gated envelope, not a free-running tone, so the patch is silent until the clock ticks.

## Lip winds (`lip/`)

`lip.py`'s `LipWind` builds the source for buzzed pipes: the whole harmonic series with Buzz setting how hard it falls away, and a `Mouth` resonance swept between `mouth_low` and `mouth_high` by a slow sine (Mouth speed), added to the tone ahead of the pipe. The sweep is how a didgeridoo talks, and the recipes' filter-cutoff LFO with high resonance. There is no tone-hole pipe, so the low-pass is only the pipe's overall roll-off.

- `natural.py`: `ConchShell` (soft, hooting, a slow swell, a cave of a room) and `Didgeridoo` (a long droning buzz held at full Legato, a strong, fast-moving mouth resonance, a lot of breath).

A brass family (trumpet, trombone, horn, tuba, the cookbook's BRASS section) would be a further `LipWind` style or its own directory, with the same shared pipe; it is not built.

## Boundaries

Unlike `tonal/vocal`, there is no formant table: the pipe is a low-pass and a resonance at the pitch, not a vowel. Unlike `tonal/keys/accordion.py`, whose reeds are ranks for a chord, a wind plays one line. The cookbook's second oscillator (a sub, an octave, a detuned copy) is a harmonic here, not a rank: `Bore`, `Reed edge`, `Buzz` and `Overtones` set which harmonics sound and how loud each is. A breath-driven tone has no filter keyboard in the cookbook's sense: Pitch tracking is that, with the cutoff multiplied by the pitch to a power.

## What NOT to assume

- Overtones is not a brightness control. It changes how many harmonics the source has; Brightness decides how many get out of the pipe. A pure sine (Overtones 0) is unchanged by Brightness unless the cutoff is below the note.
- Tongue is not an attack. Attack is how the note swells; Tongue is a separate burst of noise. A slow Attack with a clear Tongue is a soft note with a consonant, and a note slurred into the last one has neither.
- The scoop (Bend) is not vibrato: it fires once per fresh note and settles in 60 ms, so a slur has none.
- Tremolo is not the flute's vibrato. A real flute's vibrato is largely a breath pulse; Vibrato rocks the pitch and Tremolo the level, so the two, at about the same speed, are the sound of a flute and either alone is not.
- Bore is not Brightness. Bore decides *which* harmonics exist (odd only, or all); Reed edge and Buzz how loud the upper ones are; Brightness how many get out of the pipe.
- Bagpipes' Drone is not a note the phrase plays: it sits at one fixed pitch (Register) and never follows the chords.
- Nothing here is a model of fingering, overblowing or register breaks: the pitch is the oscillator's and the tone is a recipe, not a physical pipe.

## Musical references

These point to the music-theory layer for decisions *around* this voice
(pattern, pitch material, role in the arrangement and mix). They do not
cover synthesis; the sections above stay authoritative for the DSP.

- `.claude/skills/music-theory/references/instrument-idiom/winds.md` — range, breath, articulation and phrase length
- `.claude/skills/music-theory/references/orchestration/instruments-ranges-character.md`

## Sources

The cookbook recipes in [docs/todos/cookbook-extraction-todo.md](../../../../../docs/todos/cookbook-extraction-todo.md) (WOODWINDS, p.63-68: the flute is a 25% pulse through a low-pass whose envelope opens with the amp's 0.11 s attack, glide 0.015 s) set the starting values, the second oscillator read as extra harmonics, a filter envelope as `Opening`, a high-resonance filter as `Nasal` or `Mouth`; the jet as a near-sine with a ringing noise band is standard acoustics of the flute, not re-checked here against a specific source. The pipe acoustics above are Gordon Reid's, from `docs/Synthesizing Wind Instruments.pdf`. pyo documentation for `Reson`, `ButLP`, `Pow`, `Clip` and `Adsr`.
