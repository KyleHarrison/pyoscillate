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
| C1 | **Glide/portamento across notes** (remembers previous note) and **bend** | Done (see C1 status) |
| C2 | **Scale-quantise** (`grab`, `sc`) — snap any pitch stream to the rack's scale | Done (see C2 status) |
| C3 | **Strum** (per-note time spread in a chord) and **humanize** (timing ±, velocity ±) | `musical/chord` lacks strum; no humanize on any sequencer. Both are timing/state concerns → design rule 5 |
| C4 | **Glitch** — random parameter corruption by amount | Candidate for `on_evolve`/sweep-style rack tool, low priority |
| C5 | **Arp index patterns** (`notearp`, `trancearp` forward/back/preset rhythms) | Direction presets done: `ArpOrder` in `intervals.py` and `Arp.contour` (rebuild). Not done: `trancearp`'s rhythm presets (need a fast gated arp; `Arp` is a slow glide voice) and `notearp`'s octave-transposing wrap (`ArpOrder` wraps by modulo, as `trancearp` does) |
| C6 | **Chord voicing library** (75 shapes, power chord → cinematic cluster) | Check `musical/chord`; extend voicing table rather than new family |

## D. Timbre/modulation distinctions

| # | Addition | Gap |
|---|----------|-----|
| D1 | **Supersaw/unison + detune** as a tonal-voice option (`unison`, `detune`) | Confirm pad/lead cover unison spread; add as a shared param on tonal bases |
| D2 | **Wavetable position as a modulated axis** (`wt`, `wtrate`, `wtdepth`) | Pyo has no direct wavetable synth; evaluate `Osc` table morph (`NewTable`/`TableMorph`) as a Layer A mechanism |
| D3 | **FM presets with envelope** (`fm`, `fmenv`, `fmh`, `fmdecay`) | Done (see D3 status) |
| D4 | **Comb / disperse / flood effects** | Done (see D4 status) |
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

**Step 1 status (2026-10-03):** A1 (macro-param pattern) and B3 (`hit`/`value` split) are documented in `patches/AGENTS.md`. Step 3 (B1) was done ahead of step 2.

**A2 status (2026-10-03):** `scale="cutoff"` added to `SliderSpec`/`Param` (`params.py`, 4th-power taper, track 0-1, tested). Not yet adopted by any patch's brightness `Param`; do that per patch when each is next touched.

**A3 status (2026-10-03):** audit found accent already couples level and filter depth in `funk` and `fm` bass and `lead/fm`. The gap was the profile-driven bass (`groove`, `hover`, `techno`), where an accent only changed level. `AccentBass` (`bass/base.py`) adds an `accent` macro `Param` (default 0 = old sound): wider level contrast, shorter decay, more resonance on accented steps. Tested on stand-in nodes only, not auditioned by ear. `funk`/`fm` keep their own coupling.

**B2 status (2026-10-03):** the gate already had `gate_seed`. `SeededDraws` mixin (`common.py`) now gives `generative` and `canon` a `seed` Param ("Melody") and a per-instance `random.Random`; `on_evolve` re-rolls from seed + fire count. Reproducible, tested; not auditioned. `NoiseDust` still uses pyo's own randomness (not seedable this way). Racks do not list the slider yet.

**C3 status (2026-10-03):** `musical/chord` has `strum` (notes spread low to high, up to 120 ms) and `feel` (per-note timing and level jitter) Params, via a delayed trigger and envelope per note; both default 0 (unchanged sound). Tested on stand-in nodes, not auditioned. Named `feel` because `Patch.humanize` is already a title helper. Humanize is chord-only so far; the other sequencers (bass, arp, lead) still have none, and the gate's Pulse is unjittered. Racks do not list the sliders yet.

**C1 status (2026-10-03):** audit: `lead/fm` (live `glide` Param), `arp`, `pluck` (fixed 10 ms) already glided; `funk` had a fixed 20 ms; the profile-driven bass (`groove`, `hover`, `techno`), `fm` bass and `lead/lead` jumped (lead had a per-style, non-live `glide_time`). Now `Bass.glide` (seconds, sweepable, default 0) drives a shared `pitch` `SigTo` (`Bass.pitch_signal`) that groove/hover/techno, fm and funk play from (funk defaults to its 0.02); `Lead.glide` replaces `glide_time` (Mellow70s defaults 0.02). Defaults keep every voice's old sound. Tests: `bass/test_glide.py`, stand-in nodes; not auditioned. `bend` (2026-10-03): `PitchBend` mixin in `common.py` (`bend` Param, -12..12 semitones, default 0; a 60 ms scoop off a `TrigEnv`) on every `Bass` voice and `Lead`; tested on stand-in nodes plus offline renders, not auditioned. Rack sliders: `Slide` (glide + a 3-semitone scoop) and `Accent` on the bass group in `deep_house`, `forest_psytrance` and `lofi/boom_bap`; `Feel` (strum + human feel) on deep_house chords. The seed, gate and `lead/fm` sliders are per-patch only. Not done: `pluck` keeps its fixed 10 ms glide; `keys` is polyphonic.

**C2 status (2026-10-03):** `Harmony.scale` (semitones above the key; `MAJOR`, `MINOR`, `MAJOR_PENTATONIC`, `MINOR_PENTATONIC` in `harmony.py`, default `None` = off) and `Harmony.quantise(freq)` snap a pitch to the nearest scale note (ties down). `arp`, `generative` and `canon` pass every new note through it, so a rack that sets a scale keeps their free melodies in key; with no scale they sound as before. Tested in `test_harmony.py`; not auditioned. No rack sets a scale yet, and pitched patches other than these three (lead, pluck, keys) are not routed through it.

**D1 status (2026-10-03):** audit: `tonal/strings` (`spread`, SuperSaw detune) and `drone/wash` (`detune`) already expose a live detune; `tonal/pad` and `bass/reese` are placeholders; `riser` uses a fixed detune. The gap was `lead/lead`, whose oscillator detune was fixed per style. `Lead.detune` (0-0.5 semitone, default 0 = old sound, sweepable) now splits the two pulses symmetrically via two `SigTo` ratios. Tested on stand-in nodes, not auditioned. Not done: a unison *voice count* (topology, would need `rebuild=True`), and pluck/keys. Build `pad`/`reese` with a detune Param when they are implemented. `test_noise` `dust` subtests fail intermittently, with or without this change.

**D3 status (2026-10-03):** audit: `bass/fm` (Growl/Settle/Edge) and `lead/fm` (Bite/Settle/Swirl) already had the FM-index envelope; the harmonic ratio (`fmh`) was a fixed class constant. Now a live, sweepable `ratio` Param on both: `FmBass.ratio` ("Hollow", whole steps 1-4 so notes stay pitched; bark 1, grit 2) and `LeadFm.ratio` ("Colour", 1-4 in 0.01 steps; wind 2, swirl 3.01). Defaults keep the old sounds. Tests: `tonal/test_fm_ratio.py`, stand-in nodes; not auditioned. Not done: rack sliders, and `drone/fm`, `keys`, `pluck` ratios.

**D4 status (2026-10-03):** new `patches/fx.py` with three opt-in mixins, each owning its `Param`s and an `add_*(source)` helper, always built, amount default 0 (unchanged sound): `Comb` (`comb`, `comb_pitch`, `comb_ring`; pyo `Waveguide` tuned resonator), `Disperse` (`disperse`, `disperse_spread`; four parallel feedback delays at unrelated times, a diffuse smear, not a true cross-fed matrix) and `Flood` (`flood`; `Freeverb` where one amount raises size and wet share together). Prototyped on `Strings` (chain comb, disperse, flood, then gate); tests in `test_fx.py` (default off, audible change per effect). Not auditioned, no rack sliders, no "Effect add-ons" section in `patches/AGENTS.md` yet. Roll out to other voices when wanted.

## Suggested order

1. **Doc-only (cheap, high value):** A1 macro-param pattern, B3 hit/value split → `patches/AGENTS.md`.
2. **Shared infrastructure:** A2 taper on `Param`, A3 accent, B2 seed, C3 humanize/strum.
3. **New shared stage:** B1 `Gate` in `common.py` (write its concept in `patches/AGENTS.md` first; `Slot` declaration mirrors `ParamSweep`).
4. **Voice options:** C1 glide, B4 legato, C2 quantise, D1 unison.
5. **New mechanisms:** D4 comb/disperse, D2 wavetable morph.
6. **Rack layer:** E3 locks, E1 cues, E4 seeded randomiser. E2 stays in Flet.

## Open questions

- B1 (resolved): a `Gate` mixin with `Param`s on the patch; no `Slot` declaration, enabled by constructor override. Next: concept in `patches/AGENTS.md` (done), prototype on `Strings` + `SoundscapeWash`, tests, listen in Flet, then roll out.
- A2 (resolved): a `scale="cutoff"` kind alongside `scale="note"`.
- Audit before implementing: C1, C5, C6, D1, D3, D5 may already be covered — verify against existing modules first (design rule 1: extend, don't add).
- Licence: Strudel is AGPL; reimplement the *ideas* in Pyo, don't copy code.
