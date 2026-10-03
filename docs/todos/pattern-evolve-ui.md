# TODO: "Pattern" and "Progression" sections for a patch's evolve controls

Written 2026-10-04, updated for patch-level progressions. The UI work is in
`src/flet/base.py`. One backend change (task 1) depends on the progression
refactor that is in flight on `feature/pattern-refactor` (uncommitted changes
in `patches/common.py`, `projects/base.py`, `theory/progression.py`,
`harmony.py` and the racks).

## Problems today

- The evolve switch is an `AUTORENEW` icon button beside the on/off switch
  (`PatchPanel._build_control`). Nothing says what it does, and it reads as a
  refresh action.
- The evolve block (`EvolveRow`) repeats the patch's title and summary.
- The `phrase` and `progression` dropdowns sit in the generic param grid, far
  from the evolve controls that rotate them. While evolving, they go stale.
- The checklist (`EvolveRow.checkboxes`) has a fixed `height` of at most 6
  rows, so the last row is clipped and the list takes a lot of space.
- A patch with both `Phrased` and `Progressive` has **one** `Evolution`: one
  switch, one interval, and one checklist that mixes phrases and progressions
  (`evolution_choices()` concatenates both catalogs). Both axes advance on the
  same timer, and the user can't tell which rows are which.

## Design

A patch gets one bordered section per axis it has:

- **Pattern** when the patch is `Phrased`: when in the bar it plays and which
  interval above the chord root.
- **Progression** when the patch is `Progressive`: which chord root sounds in
  each bar.

A patch with both shows both sections, each with its own mode, menu, interval
and countdown. A patch with one shows one. A patch with neither is not
evolvable and shows none.

### Why a custom menu, not a `Dropdown`

`ft.Dropdown` cannot hold checkable items. Flet can build one (verified against
the Flet API):

- `ft.SubmenuButton(content=..., controls=[...])` opens a menu of controls.
- `ft.MenuItemButton(leading=ft.Checkbox(...), close_on_click=False)` is a menu
  row with a checkbox that leaves the menu open when clicked.
- Wrap the `SubmenuButton` in an `ft.MenuBar` so it has a menu host.
- `ft.PopupMenuButton` is the fallback. It closes on every select and has no
  `close_on_click`, so it is a worse fit.

This one control replaces both the dropdown and the checklist in each section.

### Behaviour, per section

- The closed control looks like a dropdown and shows the current choice.
- **Hold** mode: a row click picks that choice (writes the `phrase` or
  `progression` param) and closes the menu. Rows show a radio-style mark.
- **Evolve** mode: a row click toggles whether that choice takes part
  (`Evolution.set_choice`) and the menu stays open. The currently playing
  choice is marked, for example bold or a leading dot. "All" and "None" rows
  sit at the top.
- The mode is a `SegmentedButton` ("Hold | Evolve") in the section header. It
  replaces the icon button and maps to `Evolution.set_enabled` for that axis.
- In Evolve mode the closed label reads "3 of 8 patterns" plus the current one.
  It updates on every change.
- Menu rows keep the catalog's grouping (`category` on a phrase or
  `ChordChanges`, as `_is_grouped` does for the dropdowns today).

### Layout

```
Pattern                                  [ Hold | Evolve ]
Picks when in the bar the chords are struck...
[ Four on the floor: every beat   v ]      <- checkable menu
Changes every  [-----o-------]  2 bars     <- Evolve only
[=====.........]  Next change in 1.9 bars  <- Evolve only

Progression                              [ Hold | Evolve ]
Picks the chord changes the voice follows...
[ Four chords (I-V-vi-IV)         v ]
Changes every  [-----o-------]  8 bars
[==.............]  Next change in 6.2 bars
```

The two sections have independent intervals, so a rhythm can change every 2
bars while the chords change every 8.

### Progression and the rack

The rack-level "Progression" dropdown (`progression_dropdown`, `_set_progression`
in `PatchRackApp`) stays. It seeds every `Progressive` patch with the same
chords. A patch that evolves its own progression can drift off the rack's value,
and `_progression_value()` already shows blank when patches disagree. The
section's Hold mode lets a single patch step off the shared progression without
touching the others.

## Tasks

Status 2026-10-04: tasks 1-11 are implemented and the test suite passes (286
tests). Not yet done: running the app to look at the menu (task 12), see the
notes there.

### Backend (needs the in-flight refactor merged or settled first)

- [x] **1. One `Evolution` per axis.** Split the single `Evolution` into one
  per evolvable axis, with its own `enabled`, `bars`, `choices`, clock
  `Division` and progress. Today `Phrased.on_evolve` and `Progressive.on_evolve`
  both hang off one timer and filter the shared `choices` by catalog membership.
  Suggested shape: the patch keeps `evolutions: dict[axis, Evolution]` (axis is
  `phrase` or `progression`), and each `Evolution` takes the `Param` it moves
  and that param's catalog. `evolution_choices`, `evolution_seed` and
  `on_evolve` move onto that. Keep `Patch.evolution` as the single timer for a
  patch with a custom `on_evolve` (the non-phrased, non-progressive case such as
  the drone, bell and strings patches).
- [x] **2. Racks and presets.** `Evolve(bars, choices)` in a `Slot` names its
  axis, or is given one per axis. Check the racks that already declare it
  (deep_house, forest_psytrance, boom_bap, slowed_reverb, psyambient). The
  `preset["evolve"]` shape becomes one entry per axis. Loading an old preset
  (single entry, mixed choices) splits the choices by catalog.
- [x] **3. Shared-chord guarantee.** Two patches that evolve their progression
  with the same bars and choices must still change chord together (see the
  `Progressive` docstring). Keep the timer on the clock bar line.

### UI

- [x] **4. Header.** Remove `evolve_row.toggle` from the header row. Remove the
  duplicate title and summary from the evolve block. The header keeps title,
  summary and the on/off switch.
- [x] **5. Move the params.** In `_build_control`, skip the `phrase` and
  `progression` params in the `ResponsiveRow` when the patch is evolvable. They
  appear only in their section. A patch that isn't evolvable keeps the normal
  dropdowns.
- [x] **6. `EvolveSection`.** Rework `EvolveRow` into one bordered container per
  axis: title, the param description as subtitle, the mode `SegmentedButton`,
  the checkable menu, the interval slider and the countdown. It reads and
  writes that axis's `Evolution` and holds no values of its own. `PatchPanel`
  holds a list of sections (`evolve_rows` instead of `evolve_row`) and
  `refresh_live` and `sync_sliders` loop over them.
- [x] **7. Checkable menu.** Build the `MenuBar` > `SubmenuButton` >
  `MenuItemButton(close_on_click=False, leading=Checkbox)` control from the
  axis's catalog. Prototype first and check that the menu stays open and copes
  with about 20 rows (scrolling, width). If it doesn't, fall back to a
  dropdown plus a compact wrapping chip list.
- [x] **8. Mode behaviour.** Hold: row click writes the param and closes the
  menu. Evolve: row click calls `Evolution.set_choice` and leaves the menu
  open. Block unticking the last remaining choice.
- [x] **9. Live sync.** On each evolve step, update the closed label and the
  playing mark in the right section. Hook it to the section's `refresh`
  (already called from `PatchPanel.refresh_live`). Switching back to Hold keeps
  the choice that is playing. When a patch's progression evolves, the rack's
  `progression_dropdown` still updates (see the `refresh_live` hook in
  `PatchRackApp`).
- [x] **10. Interval and countdown.** Show the slider, the "Changes every N
  bars" label and the countdown only in Evolve mode. Keep the "Starts when the
  patch is playing" text for a stopped patch.
- [x] **11. Layout.** Put the sections under the header and above the other
  params, Pattern first, then Progression. The Output level slider stays in the
  param grid.
- [ ] **12. Verify in the running app.** Only headless checks are done (panels
  build for `Keys`, preset round trip and a legacy preset load). Run the app and check, for a patch with both, a patch
  with only a phrase, and a patch with neither:
  - Hold and Evolve switching on each axis, while playing and while stopped.
  - The two intervals running independently.
  - Countdowns and labels updating.
  - Two patches on the same progression still changing chord together.
  - Preset save and load, including an old preset.
  - That the `MenuItemButton(close_on_click=False)` rows really keep the menu
    open and that about 20 rows and the nested category submenus scroll and
    fit; if not, use the chip-list fallback in task 7.

  Then run `uv run ruff check src`.

## Decisions

- Mode control: a segmented Hold/Evolve selector (recommended) or a labelled
  "Auto-evolve" switch inside each section. The switch is a smaller change but
  makes the menu's role less clear.
- Independent intervals per axis (recommended, task 1) or one shared interval
  with two choice lists. The shared version is a smaller backend change, but the
  two sections would then show the same slider and countdown.
