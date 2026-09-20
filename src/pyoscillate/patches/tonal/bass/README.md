# Bass Patch Family

Bass patches are selected in two stages.

1. **Musical role:** decide whether the bass is a sub foundation, a repeating
   groove voice, a resonant sequence, or a sustained/animated low layer.
2. **Sonic behavior:** translate that role into register, pitch density,
   trigger timing, envelope length, harmonic content, filter movement, and
   resonance.

`BassProfile` stores the musical policy: semitone pattern, accents, decay,
resonance, and harmonic recipe. `build_bass` owns the common signal path:

```text
shared Clock -> Trig -> TrigEnv -> HarmTable/Osc -> MoogLP -> Patch output
                                      ^              ^
                               pitch pattern     fixed or LFO cutoff
```

This is why the two original patches can share implementation without
becoming the same instrument. The flat techno bass adds a free-running,
bar-long `LFO` to the filter cutoff; Deep House profiles use a fixed cutoff
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
| “dark evolving drone bass” | sustained trigger/envelope policy and slow continuous modulation, rather than a 16th-note sequencer |

Only after this synthesis-level choice do we consult the Pyo API: `Trig` and
`TrigEnv` for clocked articulation, `Osc` plus `HarmTable` for controllable
harmonics, `MoogLP` for subtractive tone shaping, and `LFO` only when the
prompt asks for continuous bar-scale motion. The same reasoning can choose a
different generator or filter for a different bass role.