# TODO: patch-logic additions from Switch Angel's strudel-scripts

Source: [strudel_source.md](strudel_source.md), plus a read of
[switchangel/strudel-scripts](https://github.com/switchangel/strudel-scripts)
(`prebake.strudel`). Strudel itself is not the point; the point is her
**musical-affordance layer**: one named, perceptual handle that expands to
several coordinated DSP parameters.

**Not a port.** Per the root [AGENTS.md](../../AGENTS.md) foundational principle,
none of these map a word to a Pyo object. Each item is a *behavioural
distinction* to add, reasoned musical → sonic → mechanism → Pyo. Strudel
numbers are grounding, not spec. Strudel is AGPL: reimplement the *ideas*, don't
copy code.

Done so far (not repeated here): macro-param pattern and `hit`/`value` split
documented; `scale="cutoff"` taper; `AccentBass`; `Gate` mixin and `Pulse`;
`SeededDraws`; stab `strum`/`feel`; bass/lead `glide` and `bend`;
`Harmony.scale`/`quantise`; arp order presets; `Lead.detune`; FM `ratio` Params;
`fx.py` (`Comb`, `Disperse`, `Flood`).

## Outstanding

### Adoption and rollout (code exists, not wired in)

- **Cutoff taper:** adopt `scale="cutoff"` in each patch's brightness `Param` as it is next touched.
- **Rack sliders:** seed ("Melody"), gate, `lead/fm`, `ratio` and the `fx.py` effects have no rack sliders; the chord `feel` sliders exist only on deep_house.
- **Scale:** no rack sets `Harmony.scale` yet; lead, pluck and keys are not routed through `quantise`.
- **Seed:** `NoiseDust` uses pyo's own randomness and is not seedable.
- **Humanize:** chord-only; bass, arp and lead sequencers have none, and the gate's `Pulse` is unjittered.
- **Glide/bend:** `pluck` keeps a fixed 10 ms glide; `keys` is polyphonic and has none.
- **Detune:** unison *voice count* is topology (`rebuild=True`), not done; `pluck`/`keys` have no detune. Build `pad`/`reese` with a detune Param when implemented.
- **FM ratio:** not on `drone/fm`, `keys`, `pluck`.
- **Effects (`fx.py`):** roll out beyond `Strings`; add an "Effect add-ons" section to `patches/AGENTS.md`.
- **Auditioning:** most of the above is tested on stand-in nodes or offline renders only. Listen in Flet.
- **Riser gate:** needs a live accelerating rate to get the most from the `Gate`.
- **Gate rollout:** only strings and the drones have been auditioned by ear.

### Not started

| # | Addition | Notes |
|---|----------|-------|
| A4 | **Style presets as macros** (`acid`, `DX`, `roller`, `spinor`) | Confirm bass/acid and fm styles cover them; add missing bundles as style subclasses, not a new mechanism |
| B4 | **Fill / legato**: extend each event to the next onset | Add a `legato`/`tie` option on pitched gated voices |
| C4 | **Glitch**: random parameter corruption by amount | Low priority; `on_evolve` / sweep-style rack tool |
| C5 | **Arp rhythm presets** (`trancearp`) and octave-transposing wrap (`notearp`) | Needs a fast gated arp; `Arp` is a slow glide voice |
| C6 | **Chord voicing library** (75 shapes, power chord to cinematic cluster) | Check `musical/stab`; extend the voicing table, not a new family |
| D2 | **Wavetable position as a modulated axis** (`wt`, `wtrate`, `wtdepth`) | Evaluate `NewTable`/`TableMorph` as a Layer A mechanism |
| D5 | **Noise hat with modulated decay**, **zap** (pitch-env sweep) | Likely covered by drums/hat and transition; verify before adding |
| E1 | **Cue / arrangement sections** (`cue`, `ar`, `track`) | Rack-level; `EvolvingGroup` exists but no explicit section/cue timeline |
| E2 | **Mute/solo per output** | UI + `GroupController` concern in `src/flet/` |
| E3 | **Parameter locks** (Elektron-style per-step overrides) | Per-step `Param` overrides on `step_pattern`; stepped, not continuous like sweeps |
| E4 | **Text/seed → patch** (`stxt`) | Rack-level seeded randomiser over a patch's `Param` min/max/step, not a new patch. Closest to the agentic goal |

Suggested order for the rest: B4 and C6 (voice options), then D2, then the rack layer (E3, E1, E4; E2 stays in Flet).
