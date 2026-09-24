# Deep House

A 122 BPM, clock-locked rack built around a four-on-the-floor kick, moving bass, offbeat minor-seventh chord stabs, hats, and accent percussion. Each role has three complementary styles; its controls shape timbre, envelope, density, and movement while the shared clock keeps the arrangement coherent.

## Shared harmony

The rack has one key and one progression, `HARMONY` in `rack.py`, and the **Key** control at the top of the app retunes it. The bass, chord stabs and tom all read the current chord from it on every note. The chord is counted in bars from the shared clock, not in each patch's own steps. So all three change chord on the same bar, whatever their Rate sliders are set to or whenever they were switched on.

- **Progression:** i–iv–♭VII–v (A–D–G–E in A) as parallel minor-seventh stabs, which is the classic deep-house "chord memory" sound. There is one chord per bar, so the four-bar loop turns twice inside each eight-bar crash phrase.
- **Bass:** re-roots its pattern on each chord. Every pattern is written as root, fifth, octave, minor third and minor seventh, which are all tones of a minor-seventh chord. The line therefore moves with the harmony and never clashes with it. *Register* lifts it an octave.
- **Chords:** each root snaps to the octave nearest D3, so the progression stays in one register instead of climbing. *Register* moves the stabs an octave down or up.
- **Tom:** its fill (fifth, fifth, minor third, root) follows the current chord, not a fixed A pentatonic. Over parallel minor sevenths, a fill fixed to the key would land on non-chord tones.

The key is saved with presets, under `_rack`.

## Drums

The **Drums** section fills out the kit around the kick, hats, clap, and percussion:

- **Snare**: a short sine body plus a louder high-passed noise rattle on the backbeat, layered under the clap, with a quiet ghost note on the last 16th that swings into the next bar. *Snap* balances rattle against body; *Tail* runs from a dry crack to a small room.
- **Tom**: a pitched body with a quick downward sweep and a faster-decaying membrane overtone, playing a sparse two-bar fill (E, E, C, A) from the minor pentatonic of the current chord (see *Shared harmony*). This adds pitched contour without competing with the kick.
- **Cymbal - Ride / Crash**: dense FM metal through a resonant band-pass with a long exponential tail. The ride keeps quarter-note top-end motion, with slow tempo-locked colour drift (*Movement*) so repeated strikes don't sound static. The crash marks the start of every eight-bar phrase. Both sit deliberately low in the mix so their tails don't mask the groove.
