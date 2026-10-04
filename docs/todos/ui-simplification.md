# UI simplification: less verbose, less overwhelming

The Flet UI (`src/flet/base.py`) shows a name, a 2-3 line description, a value
and a full-width slider for every parameter, under a six-row header. Goal:
more controls per screen, prose on demand.

Status key: [ ] todo, [x] done, [-] not needed.

## Tasks

- [x] 1. **Help text on demand.** `SliderSpec.help_text` leaves the row and
  becomes a tooltip on the label, plus a header "Descriptions" toggle that
  shows it inline again for new users. Applies to patch sliders, option
  dropdowns, group controls and the evolve section summary.
- [-] 2. **Split short name from description.** Already the case:
  `SliderSpec.description` is the short label ("Output level") and
  `help_text` the prose. No model change.
- [x] 3. **One-line slider rows.** `Label ----o---- 0.70` on one line: fixed
  label width, slider fills the middle, value at the right edge, sweep toggle
  beside it. No tick dots on fine sliders (the handler already snaps through
  `SliderSpec.from_position`); keep ticks only for coarse, stepped ones.
- [x] 4. **Main / advanced split.** `Param(..., advanced=True)` puts a
  parameter behind a per-patch "More" expander. Tag the shared tuning
  parameters; patches with none show no expander.
- [x] 5. **Collapsed patch tiles.** Each patch tile is an expandable row:
  title, one-line value summary, enable switch. A tile alone in its group (and
  every single-patch app) starts open; several in one group start folded.
  Folded tiles read out their first three slider values.
- [x] 6. **Compact Hold/Evolve section.** Drop the section description and the
  extra border; keep the segmented control, the choice menu and the
  "changes every" slider only while evolving.
- [x] 7. **Slim header.** Title, engine, pause, key, progression, master and
  tempo on two rows. Preset becomes `Preset v [Load] [Save...]`, with Save-as
  in a small dialog. Remove the "Safety-capped" line (tooltip instead).
  Smaller title.
- [x] 8. **Less nesting.** Drop the per-patch tile border and the group's
  inner padding; separate with spacing and background only.

## Notes

- Task 4: 48 fine-tuning `Param`s across the patch files are tagged
  `advanced=True`; a tile only splits when it has two or more of them and at
  least one main slider. Retag as the sound design settles.
- Task 7: Save-as moved into a dialog; the info icon in the header toggles
  inline descriptions for the whole page.
- Not verified visually: tests pass (`uv run pytest tests`, ruff clean) but
  the rendered layout needs a look in the running app.

## Validation

- `uv run ruff check src` and `uv run pytest tests/test_flet_patch_groups.py`.
- Launch a rack app and the single-patch app, check each row at narrow and
  wide widths.
