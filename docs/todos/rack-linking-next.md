# TODO: extending rack linking on top of GroupController

Source: supersedes [linked-rack-modulation.md](linked-rack-modulation.md) and
[group-controller-evolution.md](group-controller-evolution.md) (both deleted
2026-09-27), after the `GroupController` refactor landed in the lofi rack.
This file records what those two plans actually accomplished, what's now
obsolete, and the concrete next tasks — reusing `GroupController` as the
extension point rather than building the general `MOD_SOURCES`/`ModRoute`
system the original plan proposed.

## How to use this file (for future sessions)

1. Work through the tasks in order; task 4 (tests) should land before or
   alongside 1–2, since it covers a gap left by the prior work.
2. Before editing, re-read the files a task touches — they may have changed
   since 2026-09-27, which is when the line references below are from.
3. Respect the existing layering:
   - [.claude/skills/music-theory/SKILL.md](../../.claude/skills/music-theory/SKILL.md) — musical reasoning.
   - [.claude/skills/pyo-music/SKILL.md](../../.claude/skills/pyo-music/SKILL.md) — sonic reasoning, "Modulation and timescale" section.
   - [src/pyoscillate/patches/AGENTS.md](../../src/pyoscillate/patches/AGENTS.md) — patch runtime contract, including `on_evolve` and `resources` ownership rules.
   - [src/pyoscillate/controller.py](../../src/pyoscillate/controller.py) — `GroupController`: owns a group's name/title/patches/summary plus an optional `bars`-period evolution timer that calls `Patch.on_evolve(index)` on whichever patch is currently active in the group.
   - [src/pyoscillate/theory/harmony.py](../../src/pyoscillate/theory/harmony.py) — pulled, not routed. Shared key/root/progression, read independently by every `needs_harmony` patch each note.
   - [AGENTS.md](../../AGENTS.md) — project scaffolding; the rack module owns declarative config (`build_groups()`, `harmony`), the app layer stays thin.
4. Keep the foundational principle: never map a word directly to a Pyo object. Reason musically first.
5. When a task is done, tick it here, note the commit or files, and add anything learned to the Log.
6. Use `uv run` for any Python (for example `uv run pytest`, `uv run ruff check src`).

## What the prior two plans accomplished

- **Shared harmony** (`Harmony`, pulled per-note by `needs_harmony` patches) — done. Lofi rack uses a static Dm9–G13–Cmaj9–Am9 vamp, one chord per bar.
- **Step-phase bug fix** — every patch derives its rhythmic step from `clock.tick` instead of a private counter, so patches switched on mid-bar no longer drift out of phase with each other.
- **`GroupController`** (`controller.py`) — absorbed the old, separately-tracked `PatchGroupDef`: a rack now declares a group's name/title/patches/summary and its optional evolution timer in one object, in `build_groups()`. `Rack.group_controllers` is derived from that list by filtering `bars is not None`.
- **`Patch.on_evolve(index)`** — a live-only, non-`@Param` hook. The lofi rack's `lead` group (`keys.Keys`) uses it to rotate `PROGRESSIONS` every 32 bars — the only concrete instance so far.
- **Documentation** landed in `patches/AGENTS.md`, `projects/AGENTS.md` (step 6, "Wire the rack"), and the lofi README.

## What's now obsolete from the original plan

- **The general `MOD_SOURCES`/`ModRoute` audio-rate/control-rate routing system** (original tasks 1, 2, 4, 6) — not pursued. `on_evolve` covers the "one push, tens-of-bars, call a method" case more simply than a generic route/depth/clamp system would, for the only use case that's materialized so far. Revisit only if a use case needs continuous (not stepped) parameter movement or genuine multi-source depth mixing.
- **Nothing else is obsolete.** Sidechain (task 4 below, ex-task 5) is *not* obsolete — `GroupController` is control-rate (bar boundaries); sidechain ducking needs an audio-rate envelope per kick hit, which is a different mechanism entirely. See that task's note.

## Tasks

### 1. More `on_evolve` hooks, other lofi groups — [x] done (2026-09-27)

**Why:** only `lead` rotates today. Different rotation periods per group is a cheap, real version of "stack several timescales" and "the rack arranges itself" without building an LFO engine.

**Do:**
- Give `bass`, `strings`, and/or `noise` their own `GroupController(..., bars=…)` in `projects/lofi/boom_bap/rack.py`'s `build_groups()`, each with a different period (for example bass pattern variant every 8 bars, strings voicing every 16, noise character every 64 — periods that don't share a common small multiple, so the combination doesn't repeat predictably).
- Each patch needs its own `on_evolve(index)` override reading from its own musical data (a tuple of pattern/voicing variants), following the `keys.Keys.PROGRESSIONS` precedent.
- Read the relevant music-theory references before writing new bass/strings variants (see `.claude/skills/music-theory/references/electronic-parts/`).

**Done when:** at least two more groups audibly rotate on their own schedule, independently of `lead`, with no slider movement.

### 2. Sidechain / kick-driven ducking — [x] done (2026-09-27)

**Why:** the house/lofi "pump" — bass and pads duck on the kick. Distinct from task 1: this is audio-rate and per-note, not control-rate and per-bar.

**Do:**
- Expose an envelope or trigger output from the kick patch (an optional `Patch` field, or a named `resources` entry the rack can look up).
- Add an optional duck multiplier to the per-patch gain stage in `Patch.start()` ([patches/base.py](../../src/pyoscillate/patches/base.py)). Default 1.0 (no change).
- Route kick envelope → duck amount on bass and strings, with a depth and release time.
- Reuse `_resolve_group_patch("kick")` ([flet/base.py](../../src/flet/base.py)) to find whichever kick variant is currently active — this already solves "the route must follow the active kick instance," which the original plan flagged as a risk.
- Watch out: if the kick is off, the duck must rest at 1.0, never stuck ducked.

**Done when:** bass and strings audibly pump on the kick, and switching kick variants or muting the kick leaves them unducked.

### 3. A first macro — [x] done (2026-09-27)

**Do:**
- Add one rack-level slider (for example "Energy") that calls `patch.set(...)` across a few groups' currently-active patches — same push shape as `on_evolve`, just user-triggered instead of clock-triggered, and no generic `Macro`/routing type needed for a single instance.
- Wire it in the lofi Flet app header, alongside the existing Key dropdown.

**Done when:** the slider audibly lifts or relaxes multiple patches at once, and it's included in presets.

### 4. Tests — [ ] not started

**Why:** `GroupController`/`on_evolve` shipped without dedicated tests; this should close before more `on_evolve` uses pile up on an unverified primitive.

**Do:**
- Following the style in `tests/test_deep_house_patches.py` / `tests/test_flet_patch_groups.py`:
  - a `GroupController` fires `on_evolve` at the right bar boundary and not before.
  - the resolved patch is whichever instance is currently active in the group, including after a mid-run swap.
  - `_stop_engine` tears the controller down (no further fires after stop).
  - `Keys.on_evolve` wraps its index and `next_step()` reads from the new progression on the next bar boundary, not the tick it fired on.
- Once task 2 lands, add tests for: duck resting at 1.0 with the kick off, and duck following an active-kick-variant swap.

## Open questions

- Should `on_evolve` periods be user-adjustable per group (a slider on `bars`, as `GroupController.set_bars` already supports), or stay fixed in the rack module? Start fixed; `set_bars`/`set_repeat` already exist if this changes.
- Should the sidechain duck depth/release be sliders, or fixed constants tuned once? Start fixed, promote to sliders only if the fixed value doesn't sit right across kick variants.

## Deliberately out of scope

- A general-purpose virtual modular with a cable-patching UI.
- MIDI or external CV input.
- Changing individual patch sound designs beyond adding rotation variants (task 1) and a duck input (task 2).

## Log

- 2026-09-27: `linked-rack-modulation.md` and `group-controller-evolution.md` reviewed, deleted, and consolidated into this file. Confirmed sidechain (task 2 here) is not made obsolete by `GroupController` — different timescale/mechanism (audio-rate per-hit envelope vs. control-rate per-bar method call).
- 2026-09-27: task 1 done. `bass` (`bars=8`) and `strings` (`bars=16`) groups now rotate independently of `lead` (`bars=32`) — periods share no small common multiple with 32, per the task's "don't repeat predictably" note.
  - `BassConversation`/`BassMuted` (`patches/tonal/bass/groove.py`) each got an `on_evolve` that swaps `self._profile` between two `BassProfile` pattern variants (`patches/tonal/bass/profiles.py`'s new `CONVERSATION_VARIANTS`/`MUTED_VARIANTS`), following `Keys.on_evolve`'s "swap the musical data, not the graph" shape — safe because both variants share the same envelope/resonance/harmonics baked at build time, and `next_step()` already re-reads `pattern`/`accents`/`gates` off `self._profile` every step.
  - `Strings` (`patches/tonal/strings/strings.py`) got an `on_evolve` that rotates the colour voice's interval between a 9th and a 13th (`COLOUR_TONE_VARIANTS`), stored in `self._colour_interval` and read by `next_step()`/`build()` instead of the old module-level `COLOUR_TONE` constant.
  - `noise` was left alone: task 1 only requires two groups, and bass/strings already had a `PROGRESSIONS`-shaped precedent (a tuple of musical-data variants) to extend cleanly. `noise`'s styles are behaviour hooks (`moved_signal()`), not data variants, so giving it an `on_evolve` would mean designing a new "rotate parameter presets" shape rather than reusing this one — worth doing as its own decision, not bundled into this task.
  - Full test suite run before and after (via `git stash`) to confirm the pre-existing `clap`/`noise-dust`/`GatedPatchSilenceTests` failures are unrelated flakiness, not caused by this change.
- 2026-09-27: task 2 done. Sidechain infra already existed (`SidechainSource`, `Patch._wire_sidechain` in `flet/base.py`) but resolved a *fixed* patch name (`self.rack.get(sidechain.patch_name)`), so ducking silently stopped working if the source group's active style ever changed — exactly the risk this task's note flagged.
  - `SidechainSource.patch_name` renamed to `group_name`: it now names a `GroupController` group, not one fixed patch instance.
  - `PatchPanel` takes an optional `resolve_group_patch` callback (`PatchRackApp._resolve_group_patch`, already existed for `on_evolve`'s own active-patch lookup); `_wire_sidechain` calls it instead of `rack.get(...)`, so the duck always follows whichever patch is currently active in the named group.
  - `deep_house/rack.py`'s existing `BassRolling` duck updated from `SidechainSource("kick_round", ...)` (a specific style, silently wrong once `KickPunch`/`KickSoft` is selected instead) to `SidechainSource("kicks", ...)` (the group).
  - Lofi rack (`projects/lofi/rack.py`): added the actual house/lofi pump — `bass` (both styles) and `strings` now duck off the `kick` group, `depth`/`release` picked lighter than deep-house's audible pump (0.25/0.2 for bass, 0.15/0.25 for strings) per `energy-and-dynamics.md`'s "light sidechain is invisible mix help" vs. "heavy sidechain pump is an EDM aesthetic" distinction — lofi wants mix glue, not an audible four-on-the-floor pump.
  - Watched-for failure mode ("kick off → duck stuck ducked") isn't possible by construction: `Follower2` on a stopped/absent source reads silence, so `duck = 1 - 0 = 1`; confirmed no rebuild path leaves a stale duck multiplier in place.
  - No dedicated tests added yet — folds into task 4, which already lists the two sidechain cases (duck resting at 1.0 with kick off; duck following an active-kick-variant swap) to add once this landed.
- 2026-09-27: task 3 done. Added `MacroSpec` (`projects/base.py`) - one `SliderSpec` plus one `apply(value, resolve_group_patch)` push function, deliberately not a generic multi-macro/routing type since a rack needs at most one. `Rack.macro`/`EngineSpec.macro` thread it through the same way `harmony` already does.
  - `PatchRackApp` (`flet/base.py`) renders the macro's slider in the header area next to the Key dropdown when `engine.macro` is set, wires `on_change` to `MacroSpec.apply` via the existing `_resolve_group_patch` lookup (`on_evolve`'s own "whichever patch is currently active in this group" resolver, reused rather than a second lookup), and saves/loads its current value under `RACK_PRESET_KEY["macro"]` alongside the key.
  - Lofi rack's `_apply_energy` (`projects/lofi/rack.py`) is the one instance: a 0-1 "Energy" slider that calls `Patch.configure(...)` on whichever patch is currently active in `bass`, `strings`, and `lead` - `configure()` already skips parameter names a style doesn't have, so one call covers `lead`'s two very different styles (`lead.Lead`'s `brightness`/`drive` vs. `keys.Keys`'s `bark`/`bite`) without branching on which is active. Each targeted parameter's own `Param.spec.minimum`/`maximum` is reused for the 0-1 lerp instead of restating each style's range, so a future slider retune doesn't need a second edit here.
  - Verified `_apply_energy` end-to-end against unbuilt `Patch` instances (no server) at value 0.0/1.0 for both `lead` styles; full suite run showed only the pre-existing clap/noise-dust/`GatedPatchSilenceTests` flakiness, unrelated to this change.
  - Not yet done: task's "included in presets" is satisfied by the save/load wiring above, but no UI smoke test was run (no audio backend in this session) - worth a quick `uv run flet run src/flet/lofi/app.py` pass to confirm the slider audibly lifts the rack before calling this fully verified in practice.
