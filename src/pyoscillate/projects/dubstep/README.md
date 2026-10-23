# Dubstep

A 140 BPM, clock-locked rack for melodic, cinematic dubstep in the broad manner of Mt Eden Dubstep: a half-time drum pocket, a heavy tempo-synced wobble bass, and an emotional minor-key topline (piano, strings, a sung line) sitting above it. The brief is the *craft variables* of that style, not any one track: no melody, riff, vocal sample or signature patch is reproduced; every line here is original.

## Musical brief

- **Tempo/feel:** 140 BPM, felt as 70. The snare lands on beat 3 only, the kick on beat 1 with a syncopated pickup, so a bar reads as one long, heavy half-time pulse. At 140 BPM a 16th is ~107 ms and a bar ~1.71 s, so the wobble is sized in bar fractions, not Hz.
- **Harmony:** F natural minor. The progression is `i - bVI - bIII - bVII` (F - Db - Ab - Eb), two bars per chord, an 8-bar cycle, the "epic minor" loop that carries a cinematic topline. Every chord is a plain triad, so the bass keeps to root, fifth, octave and fourth (a third or seventh would clash with the major-quality chords on bVI, bIII and bVII).
- **Bass:** the sub sits at F1 and follows the chord root each bar. Long held notes with a few short stabs, so the wobble has room to be heard; the line never strikes a note on the snare (beat 3), though a held note may ring through it.
- **Topline:** slow, held notes (a sung line, a piano figure, a string swell) on chord tones and the ninth, so the melody breathes between wobble phrases instead of competing with them.
- **Form:** a looping 8-bar groove, not a full arrangement. Energy comes from which groups are switched on (breakdown = piano + strings + vocal; drop = drums + bass + topline), the bass *Wobble*/*Growl* sliders, and the riser, which lands on the downbeat of every 8-bar phrase.

Grounded in `music-theory/references/genres/electronic-edm.md` (dubstep: 138-142 BPM, half-time snare on 3, wobble as primary content; future bass/emotional crossover), `electronic-parts/bass-lines.md` (steady sparse kick means syncopated bass; register 2-3 below, filter as expression), `harmony/modal-harmony.md` (minor colour), `production-aware/energy-and-dynamics.md` (drop/breakdown contrast, sidechain pumping) and `research/style-reference-and-copyright.md` (extract tempo, groove, harmonic rhythm, density; never the melody or riff).

## Sonic brief

| Word | Perception | Mechanism chosen (not the only one) |
| --- | --- | --- |
| wobble | the bass opens and closes rhythmically, a vowel-like "wub" | a tempo-locked LFO moving a resonant low-pass over a detuned saw stack, restarted on every note so each note starts on the same phase |
| heavy / huge | weight under 60 Hz plus a wide, thick midrange | a pure sub sine under a seven-saw detuned stack, saturated after the filter |
| growl | a snarling, harmonically rich edge | resonance on the swept filter plus waveshaping after it |
| half-time | slow, heavy, spacious | kick on 1, snare only on 3, hats sparse and offbeat |
| emotional / cinematic | wistful, wide, sustained | a soft felt piano figure, a supersaw string pad on the chord, a breathy sung line on held notes |
| build | rising tension into the drop | a tempo-locked noise/pitch riser landing on the 8-bar downbeat |

## Concept-to-patch mapping

| Concept | Patch family | Decision |
| --- | --- | --- |
| Half-time kick | `drums/kick` | **Extended** with `KickDubstep`: a deep, long-bodied style playing a new `Rhythms.KICK_HALF_TIME` phrase (the graph is reused). |
| Snare on 3 | `drums/snare` | **Extended** with `SnareHalfTime` and a new `Rhythms.SNARE_HALF_TIME` phrase; the tone-plus-rattle graph is reused, with a heavier body and longer tail. |
| Sparse, skippy hats | `drums/hat` | **Extended** with `GrooveHalfTime` and a new `Rhythms.HAT_HALF_TIME` phrase. |
| Wobble bass | `tonal/bass/reese` | **New module** `reese.py` filling the placeholder `reese/` directory: a detuned saw stack plus sub with a tempo-synced filter LFO is a different topology from every existing bass (fixed cutoff, per-note envelope, FM). Two styles: `ReeseWobble` (fast 1/8 wobble, stabs) and `ReeseHeave` (slow, wide, one held note a bar). Both follow the chord and duck off the kick. New phrases `BassLines.BASS_DROP`, `BASS_DROP_B` and `BASS_HEAVE`. |
| Sung topline | `tonal/vocal` `VocalFemale` | **Reused as-is**, with a new `Leads.ANTHEM` phrase (slow held notes). |
| Piano figure | `tonal/keys` `Piano` | **Reused as-is** (starting values retuned); plays the existing `Hooks.SPARSE_HOOK` over the chord. |
| String swell | `tonal/strings` `Strings` | **Reused as-is**, ducking off the kick for the sidechain pump. |
| Build | `transition/riser` `RiserNoise`, `RiserPitch` | **Reused as-is.** |
| Chord changes | `theory/progression.py` | **Extended** with `Progressions.EPIC_MINOR`. |

## Shared constants (the rack uses)

- `bpm = 140`, `ticks_per_bar = 128`.
- `harmony = Harmony(key=Note.KEY_F, scale=Scales.MINOR)` and `progression = Progressions.EPIC_MINOR` (`i - bVI - bIII - bVII`, two bars each).
- Register anchors from `Note`: bass around `F1`, piano `F3`, sung line and strings around their families' own centres.
- Sidechain: the bass ducks off the kick group (depth ~0.5, release ~0.15 s); piano and strings duck more gently for the pump.

## Groups

- **Drums**: **Kick** (`KickDubstep`), **Snare** (`SnareHalfTime`), **Hats** (`GrooveHalfTime`). *Weight* moves kick punch and snare body together.
- **Bass**: `ReeseWobble`, `ReeseHeave`. *Wobble* (depth), *Growl* (saturation and resonance) and *Brightness* (the filter's resting point).
- **Melody**: `Piano`, `Strings`, `VocalFemale`. *Air* opens the strings and piano.
- **Build**: `RiserNoise`, `RiserPitch`.
