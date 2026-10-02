# TODO: patch-logic additions from Switch Angel's strudel-scripts

Source: [strudel_source.md](strudel_source.md), plus a read of
[switchangel/strudel-scripts](https://github.com/switchangel/strudel-scripts)
(`prebake.strudel`) on 2026-10-02. Strudel itself (Tidal-style patterns over Web
Audio) is not the point; the point is her **musical-affordance layer**: one
named, perceptual handle that expands to several coordinated DSP parameters.

**Not a port.** Per the root [AGENTS.md](../../AGENTS.md) foundational principle,
none of these map a word to a Pyo object. Each item below is a *behavioural
distinction* to add to our patch logic, reasoned musical → sonic → mechanism →
Pyo. Strudel numbers are grounding, not spec.

## What we already have vs. what the source adds

Already covered: `@Param` (one musical slider → live control), `sweep=True`,
`on_evolve`, `scale="note"`, gated/ungated families, `musical/arp|chord|generative`,
`GroupController` / `EvolvingGroup`, `Rack` Slots.

The source adds distinctions in five areas. Gaps are listed per area.

## A. Coupled-parameter macros (the `acidenv` idea)

`acidenv(x)` = one 0–1 handle driving cutoff base, env depth (`x*9`), sustain,
decay, Q together; `rlpf/rhpf` = 0–1 → perceptually-spaced cutoff (`(12x)^4`).

| # | Addition | Gap in our logic |
|---|----------|------------------|
| A1 | **Multi-target `Param`** — a `@Param` whose control writes several nodes with a defined relationship curve (already allowed, but undocumented as a pattern) | `patches/AGENTS.md` only shows single-node controls; document "macro param" as a first-class pattern and its rule: related values are derived in the one control, never mirrored |
| A2 | **Perceptual-taper helper** on `Param` (e.g. `taper="cutoff"` mapping 0–1 → Hz with a power curve) | We expose cutoff via `Brightness` per patch ad hoc; a shared taper on `params.py` removes per-patch curve code. Must live on `Param`/a class, not a module function (src AGENTS.md) |
| A3 | **Accent as coupled dynamics** — one `accent` amount scales step velocity *and* filter-env depth *and* shortens decay | Our `Step(index, hit, value)` carries value only; accent affecting timbre is not modelled |
| A4 | **Style presets as macros** — `acid`, `DX`, `roller`, `spinor` are named parameter bundles | We express these as style subclasses (profile data); confirm bass/acid and fm cover them, add missing bundles rather than a new mechanism |

## B. Gate and rhythm-density logic (`trancegate`, `tgate`, `vstruct`)

| # | Addition | Gap |
|---|----------|-----|
| B1 | **Gate stage** (Strudel `trancegate`): a shared `Gate` mixin in `common.py` (building a `Stage` like `frequency_shift()`) that chops any voice's output with a step pattern (density, seed, gate length 0.7). Model is Strudel's `struct().fill().clip(.7)`: a gated note per step, not a new voice type | `GatedVoice` couples the envelope to a source that is silent between hits; there is no way to put that envelope on a `ContinuousVoice`. Design: the stage owns its clock subscription and `TrigEnv`, and is started/stopped with the patch via `SequencerGroup`. Decision (2026-10-03): a `Gate` mixin in `common.py` owns the `Param`s (`gate`, `gate_density`, `gate_length`, `gate_seed`, `gate_rate`) and `self.add_gate(source, context)`; a rack enables it by constructor override (`Strings(gate=1.0)`), and `ParamSweep` can sweep its density, so no new `Slot` concept. It is audio-rate (`TrigEnv`), not a `Param` push: `Sweep` refreshes every 50 ms, too coarse for 16th-note edges. Users: `tonal/pad` and `texture/atmosphere` (placeholders), `texture/noise`, drones (`sub_swell` is the slow end), plus strings, arp and riser (see "B1 audit" below) |
| B2 | **Seeded density** — density param + deterministic seed so patterns are reproducible and evolvable (`rib(seed, length)`) | Our generative patches keep random state on `self`; add an explicit `seed` param and a "re-roll" via `on_evolve` |
| B3 | **Velocity-as-structure** (`vstruct`) — step value both gates (rounded) and sets level | `Step.value` exists; document and use the hit/value split consistently |
| B4 | **Fill / legato** — extend each event to the next onset | Gated voices always have independent envelopes; add a `legato`/`tie` option on pitched gated voices |

## C. Pitch-event logic

| # | Addition | Gap |
|---|----------|-----|
| C1 | **Glide/portamento across notes** (remembers previous note) and **bend** | Check `bass/groove.py` / `hover.py` coverage; add shared `glide` Param on pitched gated voices if absent |
| C2 | **Scale-quantise** (`grab`, `sc`) — snap any pitch stream to the rack's scale | `context.harmony` exists; add a quantise step usable by generative/arp patches |
| C3 | **Strum** (per-note time spread in a chord) and **humanize** (timing ±, velocity ±) | `musical/chord` lacks strum; no humanize on any sequencer. Both are timing/state concerns → design rule 5 |
| C4 | **Glitch** — random parameter corruption by amount | Candidate for `on_evolve`/sweep-style rack tool, low priority |
| C5 | **Arp index patterns** (`notearp`, `trancearp` forward/back/preset rhythms) | Compare with `musical/arp`; add direction/rhythm presets only if missing |
| C6 | **Chord voicing library** (75 shapes, power chord → cinematic cluster) | Check `musical/chord`; extend voicing table rather than new family |

## D. Timbre/modulation distinctions

| # | Addition | Gap |
|---|----------|-----|
| D1 | **Supersaw/unison + detune** as a tonal-voice option (`unison`, `detune`) | Confirm pad/lead cover unison spread; add as a shared param on tonal bases |
| D2 | **Wavetable position as a modulated axis** (`wt`, `wtrate`, `wtdepth`) | Pyo has no direct wavetable synth; evaluate `Osc` table morph (`NewTable`/`TableMorph`) as a Layer A mechanism |
| D3 | **FM presets with envelope** (`fm`, `fmenv`, `fmh`, `fmdecay`) | `bass/fm` and `lead/fm` exist; verify FM-index envelope + harmonic-ratio exposure |
| D4 | **Comb / disperse / flood effects** | Multi-tap feedback comb and delay-matrix "disperse" are new Layer A effect mechanisms; `flood` = reverb with dry reduced as amount rises (wet-dominant macro) |
| D5 | **Noise hat with modulated decay**, **zap** (pitch-env sweep) | Likely covered by drums/hat and transition; verify before adding |

## E. Rack / arrangement layer

| # | Addition | Gap |
|---|----------|-----|
| E1 | **Cue / arrangement sections** (`cue`, `ar`, `track`) — per-section activation of patterns | Rack has `EvolvingGroup`; no explicit section/cue timeline. Rack-level, not patch-level |
| E2 | **Mute/solo per output** (`o`) | UI + `GroupController` concern (`src/flet/`), not patch logic |
| E3 | **Parameter locks** (`up`, Elektron-style per-step overrides) | Per-step `Param` overrides on `step_pattern`; distinct from sweeps (stepped, not continuous) |
| E4 | **Text/seed → patch** (`stxt`) | Deterministic seed → parameter vector. Closest to our agentic goal; implement as a rack-level "seeded randomiser" over a patch's `Param`s (uses min/max/step already declared), not a new patch |

## B1 audit: where a Gate fits (2026-10-03)

Read-only audit of every module under `src/pyoscillate/patches/` (done by a subagent, not independently spot-checked).

**Good fit (holds sound open, no rhythm of its own):**
- `tonal/strings` (held chord, per-bar `Adsr`): best candidate.
- `tonal/drone/wash`: big wash, signature gated sound.
- Other drones: `Drone`, `filter`, `fm`, `sub_swell`, `sub_chaos` (soft edges needed).
- `texture/noise` Air/Surf/Barber (not `NoiseDust`); `texture/rumble` (mild).
- `musical/arp`; `transition/riser` (wants a live, accelerating rate).
- `tonal/lead/fm` Wind and `lead` Mellow70s (minor).
- Placeholders to build with a gate in mind: `tonal/pad`, `tonal/bass/reese`.

**Redundant (already has per-step on/off or note length):** all `Bass` voices
(`BassProfile.gates`), `funk`, `lead`, `pluck`, `keys` (8th tremolo), `chord`,
`texture/atmosphere`, `NoiseDust`.

**Poor fit:** `bell` and drums (the ring is the point); `generative`, `canon`,
`clock_tick` (free-running time by design); `Kick` (it is the sidechain source,
a gate would distort the duck signal).

**Design constraints found:**
1. A `Stage` only holds an output and its resources; it cannot own a clock
   `Division` or `Param`s. Use a mixin for the `Param`s and the subscription,
   plus a helper returning the `Stage`.
2. `GatedVoice.finish()` sets `self.sequencer = self._division`. Merge the gate's
   `Division` afterwards with `SequencerGroup((self._division, gate_division))`.
   `ContinuousVoice` can assign it directly as its sequencer.
3. `Drone` already replaces its sequencer with a bar `Division`; merge with it.
4. Keep the gate always built; on/off and length go through a live `SigTo`
   (never `rebuild=True`).
5. Few-ms attack/release on the table; hard edges click on near-sine subs
   (`BassChaos`, `BassDrone`, `BassHover`).
6. Step phase from `(clock.tick // steps) % 16`, not an internal counter, so it
   survives rebuilds.
7. Gate before duck and volume (post-reverb chops the tail, which is wanted).
8. Docs: a gated drone/texture blurs the gated-or-ungated rule in
   `patches/AGENTS.md`; state that a gate is an add-on and does not change a
   voice's family.

**B1 status (2026-10-03):** `Gate` mixin and shared `Pulse` implemented in `common.py` (`GatedVoice` now owns a `Pulse` too). Applied to every voice except Kick (sidechain source), bell, drums, and the free-running generative/canon/clock_tick; tests in `tests/pyoscillate/patches/test_gate.py`. Strings and the drones were auditioned and sound good; the rest are not yet auditioned by ear. Riser needs a live accelerating rate to get the most from it (not done).

## Suggested order

1. **Doc-only (cheap, high value):** A1 macro-param pattern, B3 hit/value split → `patches/AGENTS.md`.
2. **Shared infrastructure:** A2 taper on `Param`, A3 accent, B2 seed, C3 humanize/strum.
3. **New shared stage:** B1 `Gate` in `common.py` (write its concept in `patches/AGENTS.md` first; `Slot` declaration mirrors `ParamSweep`).
4. **Voice options:** C1 glide, B4 legato, C2 quantise, D1 unison.
5. **New mechanisms:** D4 comb/disperse, D2 wavetable morph.
6. **Rack layer:** E3 locks, E1 cues, E4 seeded randomiser. E2 stays in Flet.

## Open questions

- B1 (resolved): a `Gate` mixin with `Param`s on the patch; no `Slot` declaration, enabled by constructor override. Next: concept in `patches/AGENTS.md` (done), prototype on `Strings` + `SoundscapeWash`, tests, listen in Flet, then roll out.
- Does A2's taper belong on `Param` or as a `scale=` kind alongside `scale="note"`?
- Audit before implementing: C1, C5, C6, D1, D3, D5 may already be covered — verify against existing modules first (design rule 1: extend, don't add).
- Licence: Strudel is AGPL; reimplement the *ideas* in Pyo, don't copy code.
