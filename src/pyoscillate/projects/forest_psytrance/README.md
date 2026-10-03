# Forest Psytrance

A 160 BPM, clock-locked rack for forest psytrance: a dark, hypnotic subgenre of psytrance built on a deep, rolling offbeat bassline under a four-on-the-floor kick, with restrained hats and psychedelic, windy FM leads floating above. The groove is meant to be trance-inducing and organic rather than peak-time aggressive: the bass and kick lock into a tight pocket, the hats stay in the background, and the leads do the wandering.

## Musical brief

- **Tempo/feel:** 160 BPM, straight 16ths, four-on-the-floor. At this tempo a beat is 375 ms and a 16th is ~94 ms, so every envelope is sized in 16ths, not seconds.
- **Bass pulse:** the kick owns the beat; the bass is the three 16ths *between* kicks (the "e", "&" and "a" of each beat) and rests on the beat itself. That rest is the pocket: bass and kick alternate instead of stacking, which is the "rolling" motion. The line stays on the root with an octave bounce on each "a", and a minor-second (♭2) approach into the next beat once per bar.
- **Harmony:** F Phrygian. The modal colour is the ♭2 (G♭) over a static F root: a forest-psy vamp barely moves, it just leans on the ♭2 for tension. The progression is `i, i, i, ♭II` at two bars per chord (an 8-bar cycle), so the bass and lead re-root on G♭ for the last two bars of every cycle and then fall back to F.
- **Lead phrases:** 2-bar syncopated 16th phrases from F Phrygian (root, ♭2, ♭3, 4, 5, ♭6, ♭7). Notes slide into one another (portamento) and two phrase variants alternate every 8 bars via each lead's own `Evolve`, so the hypnotic loop drifts instead of repeating exactly.
- **Form:** the rack is a looping groove, not a full arrangement. Energy comes from the lead group's *Energy* control and from which layers are switched on.

Grounded in `music-theory/references/genres/electronic-edm.md` (trance/EDM tempo and structure conventions), `electronic-parts/bass-lines.md` (kick/bass interaction: a steady kick means a syncopated bass; low register; filter as expression), `electronic-parts/scales-and-modes.md` and `harmony/modal-harmony.md` (Phrygian colour), and `production-aware/arrangement-for-mix.md` (keeping the mid-range lead out of the bass and hat bands).

## Sonic brief

| Word | Perception | Mechanism chosen (not the only one) |
| --- | --- | --- |
| deep, low | weight below ~100 Hz, little upper harmonic content | near-sine harmonic recipe, low fixed low-pass, register around F1 |
| rolling | an even, unbroken 16th motion that never stops or accents hard | gated 16ths with rests only on the beat, gentle accents, a decay that fills most of a 16th |
| subtle hi-hats | present as texture, not as accents | quiet open offbeat "&"s choked by quiet closed "a"s, low level, a mix of noise and metal |
| windy | breathy, unstable, with slow air-like movement | band-passed noise tracking the note pitch, a slow drift on pitch and FM index |
| psychedelic | phasey, shimmering, swirling | a near-harmonic (slightly detuned) FM ratio whose sidebands beat against the harmonics, a slow index LFO, a dotted-8th echo |
| groovy | syncopated, sliding, locked to the kick | 16th-grid phrase with rests, portamento between notes, per-note FM "bark" |

## Concept-to-patch mapping

| Concept | Patch family | Decision |
| --- | --- | --- |
| Four-on-the-floor kick | `drums/kick` `KickPunch` | **Reused as-is**, starting values retuned: tight and punchy so the bass pocket reads clearly. |
| Deep rolling offbeat bass | `tonal/bass` `groove.py` | **Extended** with a `forest` profile (`profiles.GROOVE["forest"]`) and a `BassForest` style. The graph (`Bass.build`: HarmTable oscillator, TrigEnv, MoogLP) already does this; only the gate/pattern/accent data is new. Ducks off the kick group. |
| Subtle hi-hats | `drums/hat` `groove.py` | **Extended** with a `GrooveForest` style: a pattern of quiet open "&"s and quieter closed "a"s. The noise/metal graph and choke envelope are reused. |
| Windy, psychedelic FM leads | `tonal/lead` | **New module** `fm.py` in the existing lead family (two-operator FM with a breath noise band, a slow index LFO, portamento and an echo is a different topology from the pulse-subtractive `lead.py`, so it cannot be a style of it). Two styles: `LeadFmWind` (hollow reed-like ratio 2, sparse floating phrase) and `LeadFmSwirl` (detuned ratio 3.01, syncopated groove phrase). The family's `AGENTS.md` has a short FM section. |
| Forest atmosphere | `texture`, `tonal/drone` | **Not in this rack.** The brief asks for bass, hats and leads; the kick is the only addition (the genre cannot work without one). Atmosphere layers can be added later from existing families. |

## Shared constants (the rack will use)

- `bpm = 160`, `ticks_per_bar = 512` (the default timing resolution used by the deep-house rack).
- `harmony = Harmony(key=F)` and `progression = Progressions.PSY_VAMP` (i-i-i-bII, two bars each); `F` (pitch class 5) is added to `harmony.py` next to `A` and `C`.
- Register anchors from `theory/notes`: bass around `F1`, lead around `F4`.
- Sidechain: the bass ducks off the kick group (`depth` ~0.5, `release` ~0.1 s, inside one 16th) so the two do not stack on the beat.

## Groups

- **Kick** (`KickPunch`)
- **Bass** (`BassForest`): *Roll* control opens the filter slightly and lifts the pulse.
- **Hi-hats** (`GrooveForest`), started at volume 0.8 so the shimmer stays about 18 dB under the kick
- **Leads** (`LeadFmWind`, `LeadFmSwirl`), a group whose leads each rotate their phrase every 8 bars; *Energy* control raises FM bite, breath and echo together.
