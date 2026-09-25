# Bass Patch Family

This family is for **gated, low-register note lines**: basslines that
articulate notes on the clock and interact with the kick. Continuous low
layers live elsewhere — a sustained or slowly moving sub with a pitch centre
is a drone (`tonal/drone`), and an unpitched noise rumble is a texture
(`texture/rumble`). See "Choosing a family" in `patches/CLAUDE.md`.

Bass patches are selected in two stages.

1. **Musical role:** decide whether the bass is a sub foundation, a repeating
   groove voice, or a resonant sequence. (A sustained/animated low layer
   is a drone, not a bassline.)
2. **Sonic behavior:** translate that role into register, pitch density,
   trigger timing, envelope length, harmonic content, filter movement, and
   resonance.

`BassProfile` stores the musical policy: semitone pattern, accents, decay,
resonance, and harmonic recipe. `Bass.build_voice` (the shared family base,
`base.py`) owns the common signal path:

```text
shared Clock -> Trig -> TrigEnv -> HarmTable/Osc -> MoogLP -> Patch output
                                      ^              ^
                               pitch pattern     fixed or LFO cutoff
```

This is why the two original patches can share implementation without
becoming the same instrument. The flat techno bass adds a free-running,
bar-long `LFO` to the filter cutoff; the groove profiles (`groove.py`) use a fixed cutoff
and distinguish themselves through interval pattern, decay, and resonance.

## Prompt-to-patch choice

Extract the user's prompt into four questions before choosing a patch:

- **Function:** Is the bass carrying weight, defining groove, answering the
  kick, or supplying a moving texture?
- **Time:** Are notes clocked and articulated, or is the layer sustained and
  evolving independently?
- **Spectrum:** Should it be nearly sine-like and stable, harmonically rich
  and filtered, or noisy/inharmonic?
- **Interaction:** Should the filter and dynamics remain stable, follow the
  bar, respond to accents, or wander freely?

The answers select a profile, not a Pyo class directly. For example:

| Prompt characteristics | Patch decision |
| --- | --- |
| “subby, steady, leaves room for the kick” | low root, short harmonic recipe, stable cutoff, restrained resonance |
| “rolling deep-house bassline” | 16th-note pattern, accented downbeats, medium decay, fixed low-pass |
| “squelchy, driving techno bass” | repeated root pattern, resonant low-pass, bar-synced cutoff LFO |
| “dark evolving drone bass” | not this family: a continuous sub bed is a `tonal/drone` patch |

Only after this synthesis-level choice do we consult the Pyo API: `Trig` and
`TrigEnv` for clocked articulation, `Osc` plus `HarmTable` for controllable
harmonics, `MoogLP` for subtractive tone shaping, and `LFO` only when the
prompt asks for continuous bar-scale motion. The same reasoning can choose a
different generator or filter for a different bass role.
## Sub-families

`acid/`, `fm/`, `funk/` and `reese/` each need a different topology from
`Bass.build_voice`: a per-note filter envelope with accent/slide, FM with an
index envelope, a gated two-oscillator voice whose filter envelope swells
open on every note, and a detuned saw stack. All of them still subclass the
shared `Bass` base for scheduling and chord-following (`note_root`); only the
oscillator/filter graph itself is their own. `fm/` and `funk/` have patches
(see their `CLAUDE.md`); `acid/` and `reese/` are still placeholders. A plain
sub or harmonic bass stays in the shared core as a profile, because sub is a
register, not a family.
