# TODO: one "Pattern" section for a patch's phrase and evolve controls

Written 2026-10-04. The evolve logic (`src/pyoscillate/patches/evolve.py`) is
settled. This plan only reworks the UI in `src/flet/base.py`.

## Problems today

- The evolve switch is an `AUTORENEW` icon button beside the on/off switch
  (`PatchPanel._build_control`). Nothing says what it does, and it reads as a
  refresh action.
- The evolve block (`EvolveRow`) repeats the patch's title and summary.
- The phrase dropdown sits in the generic param grid, far from the evolve
  controls that rotate it. While evolving, it goes stale.
- The checklist of phrases (`EvolveRow.checkboxes`) has a fixed `height` of at
  most 6 rows, so the last row is clipped and the list takes a lot of space.

## Design

One bordered "Pattern" section per evolvable patch, holding the phrase picker,
the interval and the countdown. The dropdown and the checklist become **one
control**: a menu whose items are checkable and that stays open after a click.

### Why a custom menu, not a `Dropdown`

`ft.Dropdown` cannot hold checkable items. Flet does have the pieces to build
one (verified against the Flet API):

- `ft.SubmenuButton(content=..., controls=[...])` opens a menu of controls.
- `ft.MenuItemButton(leading=ft.Checkbox(...), close_on_click=False)` is a menu
  row with a checkbox that leaves the menu open when clicked.
- Wrap the `SubmenuButton` in an `ft.MenuBar` so it has a menu host.
- `ft.PopupMenuButton` is the fallback. It closes on every select and has no
  `close_on_click`, so it is a worse fit.

### Behaviour

- The closed control looks like a dropdown and shows the current phrase.
- In **Hold** mode, a row click picks that phrase (writes the `phrase` param)
  and closes the menu. A tick has no meaning here, so rows show a radio-style
  mark.
- In **Evolve** mode, a row click toggles whether that phrase takes part
  (`Evolution.set_choice`) and the menu stays open. The currently playing phrase
  is marked, for example bold or a leading dot.
- The mode is chosen by a `SegmentedButton` with "Hold" and "Evolve" (it maps
  to `Evolution.set_enabled`). It replaces the icon button.
- The closed label in Evolve mode reads "3 of 8 phrases" plus the current
  phrase. It updates on every change.

### Layout

```
Pattern                                  [ Hold | Evolve ]
Picks when in the bar the chords are struck...
[ Four on the floor: every beat   v ]      <- checkable menu
Changes every  [-----o-------]  2 bars     <- Evolve only
[=====.........]  Next change in 1.9 bars  <- Evolve only
```

## Tasks

- [ ] **1. Header.** Remove `evolve_row.toggle` from the header row. Remove the
  duplicate title and summary from the evolve block. The header keeps title,
  summary and the on/off switch.
- [ ] **2. Move the phrase param.** In `_build_control`, skip the phrase param
  (from `Phrased`) in the `ResponsiveRow` when the patch is evolvable. It
  appears only in the Pattern section. Patches that are not evolvable keep the
  normal dropdown.
- [ ] **3. `PatternSection`.** Rework `EvolveRow` into a bordered container with
  a title, the param description as subtitle, and the mode `SegmentedButton`.
  It still reads and writes the patch's `Evolution` and holds no values of its
  own.
- [ ] **4. Checkable menu.** Build the `MenuBar` > `SubmenuButton` >
  `MenuItemButton(close_on_click=False, leading=Checkbox)` control from
  `patch.evolution_choices()`. Keep the existing dropdown's grouping by role or
  category if the phrase list uses it (`_is_grouped`, `GROUPED_OPTION_THRESHOLD`).
  Add "All" and "None" rows at the top of the menu. Prototype first and check
  that the menu really stays open and handles a list of about 20 rows (scrolling,
  width). If it does not, fall back to a dropdown plus a compact wrapping chip
  list.
- [ ] **5. Mode behaviour.** Hold: row click writes the `phrase` param and closes
  the menu. Evolve: row click calls `Evolution.set_choice` and leaves the menu
  open. Block unticking the last remaining choice.
- [ ] **6. Live sync.** On each evolve step, update the closed label and the
  playing-phrase mark. Hook it to `EvolveRow.refresh` (already called from
  `PatchPanel.refresh_live`) or add a callback from `Evolution._fire`. Switching
  back to Hold keeps the phrase that is playing.
- [ ] **7. Interval and countdown.** Show the slider, the "Changes every N bars"
  label and the countdown only in Evolve mode. Keep the "Starts when the patch is
  playing" text for a stopped patch.
- [ ] **8. Layout.** Put the section under the header and above the other
  params. The Output level slider stays in the param grid.
- [ ] **9. Presets and racks.** `preset["evolve"]` and its load path keep their
  shape. `show()` must restore the mode, slider, ticks and label together.
  Check that racks declaring `Evolve(...)` open in Evolve mode.
- [ ] **10. Verify.** Run the app and check Hold and Evolve switching while
  playing and while stopped, the countdown, preset save and load, a patch with
  no phrases and a non-evolvable patch. Run `uv run ruff check src`.

## Decisions

- Recommended: Hold/Evolve as a segmented selector. The alternative is a labelled
  "Auto-evolve" switch inside the section. It is a smaller change but makes the
  dropdown's role less clear.
