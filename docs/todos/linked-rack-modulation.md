# TODO: linked, self-evolving racks (shared modulation and cross-patch links)

Source: a design conversation on 2026-09-24 comparing the deep-house rack with
how a modular-synth musician builds a patch. This file records the concepts,
the current state of the code, and an ordered plan. The goal is a rack whose
voices share musical information and whose sound changes over time without
anyone touching a slider.

## How to use this file (for future sessions)

1. Work through the tasks in order. Task 1 is a design decision that every later task depends on.
2. Before editing, re-read the files a task touches. They may have changed since this was written. The line references below are from 2026-09-24.
3. Respect the existing layering. Don't duplicate contracts between layers:
   - [.claude/skills/music-theory/SKILL.md](../../.claude/skills/music-theory/SKILL.md) holds the musical reasoning: harmony, form, arrangement energy.
   - [.claude/skills/pyo-music/SKILL.md](../../.claude/skills/pyo-music/SKILL.md) holds the sonic reasoning. It already has a "Modulation and timescale" section (around line 130). Extend that section; don't restate it.
   - [src/pyoscillate/patches/CLAUDE.md](../../src/pyoscillate/patches/CLAUDE.md) holds the runtime/patch contract, including the `resources` ownership rules.
   - [CLAUDE.md](../../CLAUDE.md) holds project scaffolding. The rack module owns `PATCH_DEFS`, and the app layer stays thin.
4. Keep the foundational principle: **never map a word directly to a Pyo object.** A "breathing" rack is a musical intent. It could be an LFO, an envelope, a slow random, or a sequenced change. Reason through it; don't jump to `Sine`.
5. When a task is done, tick it here, note the commit or files, and add anything learned to the Log.
6. Use `uv run` for any Python (for example `uv run pytest`, `uv run ruff check src`).

## Background: what "modular" means in practice

This section is short, so future sessions share the same vocabulary.

- A modular synth is a set of small single-job modules: oscillator, filter,
  VCA, envelope, LFO, sequencer, clock. Patch cables connect them.
- **Every cable carries the same kind of signal: a changing value.** The only
  difference between audio and control is speed. An LFO plugged into a filter
  cutoff moves that cutoff. A knob sets the *centre*, and cables push the
  value around it.
- A modular "patch" is the whole web of connections. Much of the music comes
  from *which signals control which other signals*, not from the voices alone.
- Experts link voices in these ways, roughly in order of sophistication:
  1. **Shared clock**, with divisions and phrase resets.
  2. **Shared pitch/key**: one root signal feeds every pitched voice.
  3. **One modulator → many destinations**, each at its own depth.
  4. **Cross-modulation**: one voice's events shape another voice. The house example is the kick ducking the bass and pads (sidechain pump).
  5. **Macros**: one "Energy" control moves several parameters together.
- Modulation source types:
  - LFOs (periodic)
  - envelopes (event-triggered)
  - random: sample-and-hold, smooth random (`Randi`), chaos (`Lorenz`)
  - modulation sequencers (per-step parameter values)
  - probability and logic
  - the performer

**Rules of thumb for automatic, periodic modulation.** Task 8 moves these into pyo-music.

- Pick the rate from the musical form:
  - beat or bar → groove
  - 8, 16 or 32 bars → phrase tension and release
  - minutes → slow evolution
- Stack several timescales on one parameter. A single LFO repeats audibly.
- Synced LFOs sound designed. Free-running ones at odd rates (for example 1/7.3 bars) drift against the grid and rarely repeat. Use both.
- Depth matters more than rate. Keep the range small around the slider's centre.
- Modulate what listeners perceive: brightness, decay, space, width. Pitch and level are risky.
- Modulating a modulator (an LFO changing another LFO's depth) is how a patch "arranges itself".

## Current state (2026-09-24)

These notes are about [src/pyoscillate/projects/deep_house/rack.py](../../src/pyoscillate/projects/deep_house/rack.py) and the shared plumbing.

- **The only shared link is the `Clock`** ([clock.py](../../src/pyoscillate/clock.py)). Every patch gets it through `needs_clock=True`. `PatchRackApp._start_engine` in [src/flet/base.py](../../src/flet/base.py) (around line 562) creates it and injects it as a build kwarg.
- **Each patch is a sealed unit.** It has its own sequencer, sound and sliders. The only way to change a parameter from outside is `Patch.set(name, value)` → `Patch.controls[name](value)` ([patches/base.py](../../src/pyoscillate/patches/base.py)). The Flet sliders call this.
- **Private modulators already exist**, but nothing outside their patch can use them:
  - the hat swell `Sine` ([drums/hat/\_\_init\_\_.py](../../src/pyoscillate/patches/drums/hat/__init__.py), around line 103)
  - the cymbal drift ([drums/cymbal/cymbal.py](../../src/pyoscillate/patches/drums/cymbal/cymbal.py), around line 135)
  - the bass cutoff `LFO` ([tonal/bass/core.py](../../src/pyoscillate/patches/tonal/bass/core.py), around line 71)
  - the drone ratio and index LFOs, and the soundscape `Lorenz` chaos
- **Harmony isn't shared:**
  - The chord patch owns a progression, `ROOTS = [0, 5, 10, 7]` (i–iv–♭VII–v), stepped inside its own callback ([musical/chord/chord.py](../../src/pyoscillate/patches/musical/chord/chord.py), around lines 49 and 88).
  - The bass has an independent `root_freq` slider and doesn't follow the chord changes.
  - The tom is "tuned to the bassline's minor pentatonic" only through hardcoded values.
  - Each patch's `rate` control changes its own step length, so a progression counted in *patch steps* drifts from the others. Shared harmony must be counted in **bars** from the clock.
- **Setter shapes vary.** Some setters assign straight to a Pyo attribute. For example, chord `brightness` does `setattr(filter_voice, "freq", value)`, which would also accept a Pyo signal. Others go through `SigTo` smoothing or a Python `state` dict. Task 1 has to deal with this.
- **Rack-level output stage.** `Patch.start()` already inserts a per-patch gain stage (`_volume_control` `SigTo`). That is a natural place to add a sidechain/duck multiplier without touching any patch.

## Tasks

### 1. Decide the modulation model — [ ] not started (design decision; ask the user)

**Why:** every later task depends on how a modulator reaches a parameter.

**Options:**
- **Control-rate.** A clock-subscribed callback computes a value (every step or every bar) and calls `patch.set(name, centre + offset)`.
  - Works today with every existing setter, and no patch needs to change.
  - Values move in steps. Patches that smooth with `SigTo` hide this.
  - Can't do fast or audio-rate effects like a sidechain pump.
- **Audio-rate.** Patches accept a Pyo signal on selected parameters, and a rack-level `Sine`/`LFO`/`Randi` is multiplied or added in.
  - Continuous movement, and it makes cross-modulation possible.
  - Patches must declare their modulatable inputs.
  - Adds ownership and rebuild complexity (see task 2).
- **Recommended: a hybrid.** Start control-rate (tasks 2–4) to prove the routing and UI model. Add audio-rate inputs only where they're needed (task 5, sidechain).

**Also decide:**
- **Slider semantics.** The slider stays the *centre* and modulation is an offset, scaled by a per-route depth. Confirm this, and decide whether the UI shows the live modulated value.
- **Whether presets store routes and depths**, or only slider values. Presets live in `src/flet/<project>/presets/` via `PresetStore`.
- **Verify:** whether `SigTo.value` accepts a Pyo signal. It isn't in the local pyo-api references, so check it with `uv run python -c "..."` before relying on it for audio-rate.

**Done when:** the decision and its reasoning are recorded in the Log, and patches/CLAUDE.md has a short note on it (see task 8).

### 2. Rack-level modulation sources and routes — [ ] not started (depends on 1)

**Do:**
- Add a small module, for example `src/pyoscillate/modulation.py` next to `clock.py`, with source types:
  - **tempo-synced LFO**: period in bars, a shape (sine, triangle, ramp, square), and a phase
  - **free-running LFO**: period in seconds
  - **clocked sample-and-hold**: a new random value every N bars or steps
  - **smooth random**
  - **stepped modulation sequencer**: a list of values, advanced on a clock division
- Add a declarative route type, such as `ModRoute(source, patch_name, param, depth)`. Racks declare `MOD_SOURCES` / `MOD_ROUTES` in the rack module next to `PATCH_DEFS`, so the app layer stays thin.
- In `PatchRackApp`:
  - create the sources when the engine starts
  - apply routes to whichever patches are running
  - **re-apply routes when a patch is started, rebuilt, or restored from a preset**
  - tear everything down when the engine stops
- Clamp every modulated value to the parameter's `SliderSpec` min and max.
- Ownership: the rack owns the modulator objects and must retain them for as long as the engine runs. Follow the same rules as `Patch.resources`: named locals, and nothing anonymous inside another constructor.

**Done when:** one route (for example, a 16-bar LFO on chord `brightness`) moves the parameter audibly, survives a patch rebuild, and stops cleanly when the engine stops.

### 3. Shared harmony (key/root source) — [x] done 2026-09-25 (turned out not to need 2)

**Why:** this is the biggest musical gain. The bass, chords and tom should move together through the progression.

**Do:**
- Read the music-theory skill first, especially:
  - [electronic-parts/bass-lines.md](../../.claude/skills/music-theory/references/electronic-parts/bass-lines.md)
  - [electronic-parts/chords-and-voicing.md](../../.claude/skills/music-theory/references/electronic-parts/chords-and-voicing.md)
  - [electronic-parts/scales-and-modes.md](../../.claude/skills/music-theory/references/electronic-parts/scales-and-modes.md)
- Add a rack-level harmony source. It holds the key, the progression and the current chord root, and it advances on **bar** boundaries from the clock, not on patch steps.
- Move the chord's `ROOTS` progression out of `chord.py` and into the harmony source, or the rack module. Keep a fallback so `chord.py` still works standalone outside a rack.
- Make the bass, chord and tom read the current root from the harmony source.
- Decide the bass's relationship to the chord musically: root, fifth, or pedal. Don't just copy the chord root.
- Decide what the per-patch `root_freq` sliders become. Options: remove them, turn them into a rack-level "Key" control, or turn them into octave or offset controls.

**Done when:** a chord change is heard in the bass and tom on the same bar, and changing the rack key moves all three together.

### 4. First demo: one phrase LFO, many destinations — [ ] not started (depends on 2)

**Do:**
- Route a 16-bar synced LFO to the chord `brightness`, the hat brightness, and the bass `cutoff`. Give each a different depth, and consider a phase offset per destination.
- Add a slow free-running random on one parameter (for example, cymbal colour) so the rack doesn't loop exactly.
- Record in the deep-house README what the listener should hear: the whole rack opening and closing over each phrase.

**Done when:** the rack audibly "breathes" over 16 bars with no slider movement, and the change stays subtle, not a full-range sweep.

### 5. Sidechain / cross-modulation from the kick — [ ] not started (depends on 1 and 2; needs audio-rate)

**Do:**
- Expose a trigger or envelope output from the kick patch. For example, add an optional `Patch` field or a named entry in `resources` that the rack can look up.
- Add an optional duck multiplier to the `Patch.start()` gain stage in [patches/base.py](../../src/pyoscillate/patches/base.py). The default is 1.0, meaning no change.
- Route: kick envelope → duck amount on bass and chords. Give it a depth and a release time.
- Watch out:
  - Kick variants are swapped via groups (round, punch, soft), so the route must follow whichever kick is active.
  - If the kick is off, the duck must rest at 1.0 (no gain change).

**Done when:** the bass and chords pump on the kick, and switching kick variants or muting the kick doesn't leave them stuck ducked.

### 6. Macros — [ ] not started (depends on 2)

**Do:**
- Add a macro type in the rack module: `Macro(name, routes=[(patch, param, depth), ...])`.
- In `PatchRackApp`, render the macros as rack-level sliders in the app header.
- Deep-house example: **Energy** raises hat brightness, bass cutoff and chord brightness, and shortens the ride's decay.
- The macro moves the *centre* of each route. It should combine cleanly with LFO modulation from task 2.

**Done when:** one Energy slider audibly lifts or relaxes the whole rack, and presets save it.

### 7. Structure: meta-modulation, phrase logic, probability — [ ] not started (depends on 2)

**Do:**
- Let a source's depth or rate be the destination of another source. Example: a 64-bar LFO that fades the 16-bar brightness LFO in and out.
- Add phrase logic: actions every N bars, such as a fill, a filter reset, or a mute. The cymbal crash already marks 8-bar phrases, so reuse that timing idea.
- Add per-step probability to at least one percussion patch (ghost notes). Keep the random state across updates (patches/CLAUDE.md rule 5).
- Read [form/narrative-and-transitions.md](../../.claude/skills/music-theory/references/form/narrative-and-transitions.md) before choosing phrase lengths.

### 8. Documentation — [ ] fold in as tasks land

- **pyo-music SKILL.md**, "Modulation and timescale" section: add the rack-level rules from the Background section above. Cover:
  - choosing the rate from musical form
  - stacking timescales
  - synced vs free-running
  - depth over rate
  - perceptual destinations
  - one source feeding many destinations
- **patches/CLAUDE.md**: add a short contract note once task 1 is decided. Cover:
  - how a patch declares modulatable parameters
  - that modulated values stay within `SliderSpec` bounds
  - that rack-level modulators follow the same ownership rules
- **CLAUDE.md**, new project workflow step 5 ("Wire the rack"): mention `MOD_SOURCES`, `MOD_ROUTES` and `MACROS` next to `PATCH_DEFS`.
- **deep-house README**: add the modulation map (source → destinations, depth, musical purpose).

### 9. Tests — [ ] fold in as tasks land

- Unit tests:
  - a route calls the right setter with a clamped `centre + depth * value`
  - routes are re-applied after a patch rebuild
  - the engine stop tears down every source
- Follow the existing test style in [tests/](../../tests/), such as `test_deep_house_patches.py`.
- Perceptual checks: once the render-and-verify helper from [synth-patch-ai-gist.md](synth-patch-ai-gist.md) task 2 exists, check that the task 4 LFO moves the spectral centroid over a 16-bar render.

## Open questions

- How should the Flet UI show a modulated parameter? Options: a static slider with a moving indicator, a depth control per route, or nothing beyond the slider.
- Should routes be editable in the app (a mini patch-bay UI), or declared only in the rack module? Start declared-only.
- Is control-rate update granularity per step or per bar? Is it fine enough for brightness sweeps, or is audio-rate needed there too?

## Deliberately out of scope

- A general-purpose virtual modular with a cable-patching UI. The aim is musical links inside a genre rack, not a VCV Rack clone.
- MIDI or external CV input.
- Changing individual patch sound designs. This plan only connects existing patches.

## Log

- 2026-09-24: design conversation held; this plan written. No code changed yet.
- 2026-09-25: task 3 done without task 2. Harmony is *pulled*, not routed: `Harmony` ([harmony.py](../../src/pyoscillate/harmony.py)) is plain data (key, progression, bars per chord). Patches that take `harmony=` look up `harmony.chord_freq(centre, clock.bar_index)` on every note, so a rebuild or a preset restore needs no re-apply step. `Clock.bar_index` is the shared song position. Racks opt in with `PatchDef(needs_harmony=True)` and `EngineSpec(harmony=...)`, and the app then shows a Key dropdown that is saved in presets as `_rack.key`. Decisions:
  - roots snap to the octave nearest each part's register centre, so the progression never climbs out of range
  - the bass re-roots its pattern on each chord (the patterns only use minor-seventh chord tones)
  - the tom follows the chord, not the key
  - the `root_freq` sliders became octave `Register` sliders
  - the harmonic rhythm is one chord per bar; before this, the chord cycled all four chords inside one bar
  - standalone patches fall back to a module-level `FALLBACK_HARMONY`
  - tests: `tests/pyoscillate/test_harmony.py`, plus the same-bar and key-change tests in `tests/test_deep_house_patches.py`
- Found while doing task 3, not fixed: each patch's *rhythmic* position is still its own `state["step"]` counter, so a patch switched on mid-bar starts its pattern off the downbeat (for example, the chord's offbeat stabs can land on the beat). Deriving the step from the clock tick (`clock._tick // division.steps`) would fix it rack-wide.
- Task 3's "depends on 2" note was wrong: pulling from a shared object avoids routing entirely. Task 2's routes may later modulate `Harmony` inputs, but they aren't needed for it.
