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

## Jet winds (`flute/flute.py`)

A flute has no reed. The breath is a jet that splits on the embouchure edge and sets the pipe's air ringing, so the tone is the pipe's own resonance: almost a sine at the pitch, a few weak overtones that fall away fast, and a band of jet noise ringing around the pitch. `JetWind` builds the source as `partials` sines at integer multiples of the pitch, each weighted by Overtones to the power of its number; the weights are normalised so Overtones changes the colour (from a pure, hollow sine to a fuller, reedier tone) and not the loudness. Flutter is the flutter tongue, a fast roll of the level (12 to 40 Hz) from full to `1 - Flutter`, present for the whole note.

`Flute` is a `JetWind` with a register of C4 to C6, a soft attack, a light blooming vibrato, a faint flat scoop and a little tongue. `flute/flute_phrases.py` holds the flute's tunes: long, fixed melodies (`FluteTunes`, written note by note as `Phrase`s) that belong to one instrument and are injected into the flute's Pattern dropdown (`FlutePhrases`: the tunes first, then every hook and lead a wind line plays). This is the one place a patch family keeps its own phrases, because a tune is a piece for one instrument; a short figure any voice could play still goes in `theory/phrase/`. A piccolo or a penny whistle is a style on the same base (an octave up, a sharper tone, a harder tongue).

## Design alternatives

Jet wind (`flute/flute.py`):
    sines at the pitch's harmonics, weighted by Overtones → resonated breath → pipe low-pass → tongue → breath pulse and flutter → room

Reed wind (clarinet, oboe, bassoon, saxophone), not implemented:
    a band-limited pulse wave at the pitch with a settable width as the reed's waveform (a clarinet's near-square is the hollow, odd-harmonic cylinder; an oboe's or bassoon's narrower pulse is the conical bore's nasal full set), through the same pipe, breath and tongue. A reed base would sit between `Wind` and the styles as `JetWind` does, with the pulse width as its own control (Reed shape) and the double reed's nasal edge as a formant-like resonance, beside the shared controls. The recipes' second oscillator is a sub or an octave of the first; it is a rank, as in `tonal/keys/sustained.py`.

Drone winds (bagpipes, didgeridoo), not implemented:
    a reed or a lip source with a fixed-pitch drone sounding under the line, as `HurdyGurdy` keeps a tonic string. A bagpipe's chanter never stops (full Legato, no tongue) and the bag's pressure gives its swell; a didgeridoo's resonance is a slow sweep of the pipe's cutoff, which is Brightness swept.

Conch and horn-like lip winds, not implemented:
    lips buzzing against a shell or a pipe: a sawtooth-like source through a heavily resonant, slowly opening pipe. It shares the pipe, breath and tongue with the others and wants a lip-buzz control rather than a reed one; it may belong with brass when that family exists.

## Boundaries

Unlike `tonal/vocal`, there is no formant table: the pipe is a low-pass and a resonance at the pitch, not a vowel. Unlike `tonal/keys/accordion.py`, whose reeds are ranks for a chord, a wind plays one line. A breath-driven tone has no filter keyboard in the cookbook's sense: Pitch tracking is that, with the cutoff multiplied by the pitch to a power.

## What NOT to assume

- Overtones is not a brightness control. It changes how many harmonics the source has; Brightness decides how many get out of the pipe. A pure sine (Overtones 0) is unchanged by Brightness unless the cutoff is below the note.
- Tongue is not an attack. Attack is how the note swells; Tongue is a separate burst of noise. A slow Attack with a clear Tongue is a soft note with a consonant, and a note slurred into the last one has neither.
- The scoop (Bend) is not vibrato: it fires once per fresh note and settles in 60 ms, so a slur has none.
- Tremolo is not the flute's vibrato. A real flute's vibrato is largely a breath pulse; Vibrato rocks the pitch and Tremolo the level, so the two, at about the same speed, are the sound of a flute and either alone is not.
- Nothing here is a model of fingering, overblowing or register breaks: the pitch is the oscillator's and the tone is a recipe, not a physical pipe.

## Musical references

These point to the music-theory layer for decisions *around* this voice
(pattern, pitch material, role in the arrangement and mix). They do not
cover synthesis; the sections above stay authoritative for the DSP.

- `.claude/skills/music-theory/references/instrument-idiom/winds.md` — range, breath, articulation and phrase length
- `.claude/skills/music-theory/references/orchestration/instruments-ranges-character.md`

## Sources

The cookbook recipes in [docs/todos/cookbook-extraction-todo.md](../../../../../docs/todos/cookbook-extraction-todo.md) (WOODWINDS, p.63-68: the flute is a 25% pulse through a low-pass whose envelope opens with the amp's 0.11 s attack, glide 0.015 s) set the starting values; the jet as a near-sine with a ringing noise band is standard acoustics of the flute, not re-checked here against a specific source. pyo documentation for `Reson`, `ButLP`, `Pow`, `Clip` and `Adsr`.
