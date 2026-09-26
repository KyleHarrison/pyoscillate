# Strings

## Sonic function

A string ensemble is a sustained chordal voice imitating a section rather than a solo instrument: several detuned voices per note, a gradual attack rather than a struck one, and ensemble chorus that makes the chord shimmer instead of sitting static. Unlike `tonal/keys`, there is no percussive strike or decaying ring - the chord holds for as long as the harmony does, and moves between chords by cross-fading rather than re-articulating.

## Minimal architecture

gate (once per chord)
→ several detuned voices per chord tone (root, fifth, octave, one colour tone)
→ low-pass for warmth
→ slow attack / release envelope (no struck transient)
→ ensemble chorus
→ optional reverb

## Detuned-ensemble synthesis

A classic string machine (e.g. the Solina/ARP string ensemble lineage) gets its section sound from many sawtooth oscillators per note, each slightly mistuned, run through a bucket-brigade chorus/ensemble effect. No single oscillator is ever quite in tune with its neighbours, so the combined tone beats and shifts continuously - the same acoustic phenomenon that makes a real string section, with dozens of individually-imprecise players, sound wider and less static than one instrument.

`strings.py` gets the "several detuned voices" stage from pyo's `SuperSaw` (a JP-8000 "Supersaw" emulation): seven sawtooth oscillators per call, already detuned and balanced between a central oscillator and its sidebands via one `detune` argument, rather than hand-building and retaining seven separate oscillators per chord tone. `Chorus` (a modulated multi-tap delay) is then the ensemble/chorus stage on top of the mixed chord, standing in for the string machine's BBD ensemble circuit.

## Voicing against the rack harmony

`Harmony.chord_freq` gives one root frequency per bar; it carries no chord-quality information (major/minor/7th), so a colour tone written as a fixed interval above that root can occasionally be a passing dissonance against an unusual chord quality (e.g. a fixed major-9th color tone against a diminished chord). `strings.py` keeps its default voicing to root + fifth + octave, which stays consonant against any triad or seventh chord regardless of quality, and exposes the colour tone (a major 9th above the root) as a separate, blendable voice via its own parameter rather than baking it into the default chord - see `keys.py`'s `CHORDS` for the alternative of hand-writing exact per-bar voicings tied to one project's specific progression, which is more precise but only reusable inside that one rack.

## Envelope

No struck transient: the amplitude envelope is a plain `Adsr` (attack, decay, sustain held at 1, release) retriggered once per bar (or once per chord, when a project's `Harmony.bars_per_chord` is greater than one) rather than every clocked step. A long attack is the "bowed swell" the sonic function calls for; a long release lets one chord's tail cross-fade under the next chord's attack instead of cutting cleanly.

## Parameter logic

- brightness: how much top end survives the low-pass, i.e. how "close" or "covered" the section sounds
- attack / release: how gradually the chord swells in and lingers out
- spread: `SuperSaw`'s own `detune` - how far the ensemble's inner oscillators drift from the central pitch
- shimmer: `Chorus`'s `depth`/`feedback` - how strongly the ensemble effect wobbles the sound
- colour: blend level of the extra major-9th voice above the root

## Design alternatives

Supersaw ensemble (`strings.py`):
    `SuperSaw` per chord tone (root, fifth, octave, blendable 9th) + low-pass + `Chorus` + `Adsr` with no struck attack

Classic string-machine, not implemented yet:
    several individually-retained detuned `SawTable`/`Osc` voices per note instead of one `SuperSaw` call each, for independent per-voice control (e.g. a slow individual drift LFO per oscillator) beyond what `SuperSaw`'s single `detune` argument exposes

Bowed physical-model strings, not implemented yet:
    a bowed/friction excitation model rather than a detuned-oscillator ensemble, for a soloistic rather than section sound - closer to a real bowed instrument's noisy attack transient

## Boundaries

Closely related to `pad/` (string machines are where the classic pad sound came from): keep `strings.py` for a recognisable section timbre and per-bar chord-following, and reach for `pad/` when the goal is a slower-breathing, more abstractly evolving sustained texture that isn't meant to read as "a string section". Unlike `tonal/keys`, `strings.py` has no struck attack or decaying ring - it is closer to a continuously-held pad than to a percussive keyboard, even though it is still a `GatedVoice` that re-articulates on the harmony's clock rather than a free-running `ContinuousVoice`.

## What NOT to assume

- More detune is not automatically "better" ensemble character. Past a point `SuperSaw`'s `detune` reads as visibly out of tune rather than as a wide section.
- The colour tone is not free harmonic information: it is one fixed interval above the root, and can clash with a chord quality it wasn't chosen for. Treat it as a controllable colour, not a music-theoretically exact extension.

## Musical references

These point to the music-theory layer for decisions *around* this voice
(pattern, pitch material, role in the arrangement and mix). They do not
cover synthesis; the sections above stay authoritative for the DSP.

- `.claude/skills/music-theory/references/instrument-idiom/strings.md` — section writing and range
- `.claude/skills/music-theory/references/electronic-parts/chords-and-voicing.md` — open voicings and voice leading
- `.claude/skills/music-theory/references/orchestration/voicing-and-texture.md`

## Sources

pyo 1.0.6 documentation, `SuperSaw` ("Roland JP-8000 Supersaw algorithm... 7 sawtooth oscillators detuned against each other") and `Chorus`. General synthesis knowledge of string-machine/ensemble design (multiple detuned saws per note through a chorus/ensemble circuit, as in the Solina/ARP string-ensemble lineage) is well established but not re-checked here against a specific fetched source.
