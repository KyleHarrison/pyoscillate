# TODO: rack-level group controller for periodic, infrequent evolution

Source: a design conversation on 2026-09-27 about the lofi rack's keys chord
progression feeling repetitive. Related to, but narrower than,
[linked-rack-modulation.md](linked-rack-modulation.md) — that file's task 7
("phrase logic: actions every N bars") describes the same shape of problem
in more generic modulation terms. This file specifies one concrete, minimal
mechanism: a rack-level controller that calls a plain method on a group's
currently-active patch every N bars. It is not the `MOD_SOURCES`/`ModRoute`
system from that file's task 2 — no depth, no audio-rate signal, no
parameter routing. Just "call this hook, infrequently, on whichever patch is
switched on right now."

## How to use this file (for future sessions)

1. Work through the tasks in order. Task 1 is the shared primitive; task 2
   is its first concrete use (keys). Later tasks are optional follow-ups.
2. Before editing, re-read the files a task touches — they may have changed
   since 2026-09-27, which is when the line references below are from.
3. Respect the existing layering:
   - [src/pyoscillate/patches/CLAUDE.md](../../src/pyoscillate/patches/CLAUDE.md) — the patch runtime contract. This adds one new hook to it (task 1).
   - [src/pyoscillate/clock.py](../../src/pyoscillate/clock.py) — reuse `Clock.subscribe`/`Division` as-is; don't add new scheduling primitives.
   - [src/pyoscillate/harmony.py](../../src/pyoscillate/harmony.py) — the closest existing precedent for "rack-level shared state, pulled by patches, plain data." The controller differs in that it *pushes* (calls a method) rather than being pulled, because it targets a specific currently-active patch, not "every pitched patch."
   - [CLAUDE.md](../../CLAUDE.md) — project scaffolding; the rack module owns declarative config (`PATCH_GROUPS`, `HARMONY`, and now `GROUP_CONTROLLERS`), the app layer stays thin.
4. Keep the foundational principle: don't collapse "repetitive" straight into a specific DSP fix. The chosen mechanism here is a *musical-structure* change (rotate which progression is comping), not a sonic one — it belongs in the patch's own musical data, not in the controller.
5. When a task is done, tick it here, note the commit or files, and add anything learned to the Log.
6. Use `uv run` for any Python (for example `uv run pytest`, `uv run ruff check src`).

## Design (agreed 2026-09-27)

- **`GroupController`** (new, `src/pyoscillate/controller.py`): holds `groups: tuple[str, ...]` (the `PatchGroupDef.name`s it watches) and `bars: int` (period; infrequent — tens of bars, not beats). It is not plain data like `Harmony`: it has a lifecycle, `start(clock, resolve)` / `stop()`, because it owns a `Clock.subscribe(...)` `Division`.
  - `start()` subscribes at `clock.bar * self.bars` and increments its own counter on each fire.
  - On fire, for each watched group name it calls `resolve(name)` to get the group's **currently active** patch instance (round-robin group switching means this can change at any time — the controller must resolve by name at fire time, never bind to an instance at declare time), then calls `patch.on_evolve(index)` on it.
  - `resolve` is supplied by the app (`PatchRackApp`), reusing whatever internal lookup already knows which patch instance is "on" for a group's UI switch.
- **`Patch.on_evolve(self, index: int) -> None`** (new, `patches/base.py`): a no-op default hook, deliberately not a `@Param` — no slider, no preset entry, not a user-facing control. It is a plain live method call, the same relationship the UI sliders already have to `Patch.set()`, just driven by the controller's timer instead of a widget. `index` is the controller's own fire count; a patch reads it as an index into its own musical data (e.g. `index % len(self.PROGRESSIONS)`) without needing to know about bars, clocks, or the controller's period.
- **Rack wiring**: `GROUP_CONTROLLERS = (GroupController(groups=("lead",), bars=32),)` declared in `projects/lofi/rack.py` next to `HARMONY`/`PATCH_GROUPS`. `EngineSpec` gets a `group_controllers: tuple[GroupController, ...] = ()` field (same pattern as its existing `harmony` field).
- **App wiring** (`src/flet/base.py`): `PatchRackApp.__init__` stashes `self.group_controllers = engine.group_controllers` (mirrors `self.harmony`, ~base.py:388-390). `_start_engine` (~589-601) starts each controller once `self.clock` exists. `_stop_engine` (~620-622) stops each controller alongside `self.clock.stop()`.
- No new `needs_*` build-kwarg flag. The controller is not injected into `build()` — it calls a method on the already-built, live instance, exactly like a slider does.

## Tasks

### 1. `GroupController` primitive + `Patch.on_evolve` hook — [ ] not started

**Do:**
- Add `src/pyoscillate/controller.py` with `GroupController` as designed above. Ownership rule: the app must retain each started controller for as long as the engine runs (same rule as `Clock`/`Tempo` in `PatchRackApp`).
- Add `Patch.on_evolve(self, index: int) -> None` no-op to `patches/base.py`, documented as a live-only, non-`@Param` hook.
- Add `EngineSpec.group_controllers: tuple[GroupController, ...] = ()`.
- Wire `PatchRackApp.__init__`, `_start_engine`, `_stop_engine` in `src/flet/base.py` as above. `_start_engine`'s `resolve` callback must return the group's *currently active* patch instance, not a fixed one — check whatever mechanism already exists for group on/off switching (`PatchGroupDef`/panel code) rather than inventing a second one.
- Clamp nothing here — `on_evolve` implementations own their own index wraparound (e.g. `%= len(...)`), since there's no shared numeric range to clamp against.

**Done when:** a controller with a synthetic `on_evolve` (e.g. printing/logging its index) fires every N bars, survives the group's active patch being swapped mid-run, and stops cleanly when the engine stops.

### 2. Keys: rotate the chord progression — [ ] not started (depends on 1)

**Do:**
- In `src/pyoscillate/patches/tonal/keys/keys.py`: rename the single `CHORDS` tuple to a class-level `PROGRESSIONS: ClassVar[tuple[tuple[tuple[int, ...], ...], ...]]` — a tuple of progressions, each shaped like the current `CHORDS` (a tuple of 4 semitone-tuples, one per bar of the vamp). Keep the current progression as `PROGRESSIONS[0]` so existing presets/behaviour don't silently change.
- Add `self._progression_index = 0` in `_reset()` — state kept explicit per `patches/CLAUDE.md` rule 5, not a `@Param`.
- Override `on_evolve(self, index)`: `self._progression_index = index % len(self.PROGRESSIONS)`.
- Update `next_step()` to read `self.PROGRESSIONS[self._progression_index]` instead of the module-level `CHORDS`.
- Write at least one more progression in `PROGRESSIONS`. Read [.claude/skills/music-theory/references/electronic-parts/chords-and-voicing.md](../../.claude/skills/music-theory/references/electronic-parts/chords-and-voicing.md) first — the new progression should keep the same close-voicing/common-tone discipline the docstring already describes for the current one (see `keys.py`'s module docstring and the comment above `CHORDS`).
- In `projects/lofi/rack.py`: add `GROUP_CONTROLLERS = (GroupController(groups=("lead",), bars=32),)` (confirm `"lead"` is the correct group name — it was `keys`/`lead` in the rack's `PATCH_GROUPS` as read on 2026-09-27; re-check) and pass it into the rack's `EngineSpec`.

**Done when:** running the lofi rack, the keys progression audibly changes every 32 bars without any slider movement, and switching the `lead` group to a different patch instance mid-run doesn't crash or leave the controller pointed at a stale instance.

### 3. Documentation — [ ] fold in as tasks land

- **patches/CLAUDE.md**: add `on_evolve` to the patch contract section (it's a third live-update path alongside `@Param` controls and `Patch.set()`, but controller-driven and not user-facing).
- **CLAUDE.md** new-project workflow step 5 ("Wire the rack"): mention `GROUP_CONTROLLERS` next to `PATCH_DEFS`/`MOD_SOURCES` (if task 2 of `linked-rack-modulation.md` has landed by then).
- **lofi README**: note the 32-bar progression rotation as a listener-facing fact, same as `linked-rack-modulation.md` task 4 asks for its LFO destinations.

### 4. Tests — [ ] fold in as tasks land

- Unit tests, following the style in `tests/test_deep_house_patches.py`:
  - a `GroupController` fires `on_evolve` at the right bar boundary and not before
  - the resolved patch is whichever instance is currently active in the group, including after a swap
  - `_stop_engine` tears the controller down (no further fires after stop)
  - `Keys.on_evolve` wraps the index and the resulting `next_step()` reads from the new progression on the very next bar boundary, not the tick it fired on

## Open questions

- Should `GroupController` support more than one group name meaningfully changing together (e.g. keys and bass evolving in lockstep), or is one controller per group the common case? Start with the single-group case (task 2) and revisit if a second use case appears.
- Should the fire count (`index`) reset on engine stop/start, or persist via a preset? Start with reset-on-start (simplest); revisit only if a user notices the progression restarting sounds wrong.
- Whether `on_evolve` should ever need the `Clock`/`Harmony` objects (e.g. to key a change off `bar_index` directly) instead of just an opaque index. Start with the opaque index; it's simpler and keeps `on_evolve` decoupled from clock internals.

## Deliberately out of scope

- Depth/rate LFO-style modulation — that's `linked-rack-modulation.md` tasks 2 and 4.
- A patch-bay UI for editing controllers — declared only, in the rack module, same as that file's open question resolves for routes.
- Any change to `Harmony`'s pull-based model. The controller pushes because it targets one specific active-patch instance per group; harmony stays pulled because every pitched patch reads it independently.

## Log

- 2026-09-27: design discussed and agreed; this plan written. No code changed yet.
