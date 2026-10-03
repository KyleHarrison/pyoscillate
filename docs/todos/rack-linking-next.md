# TODO: tests for GroupController, `on_evolve` and sidechain ducking

`GroupController` (`src/pyoscillate/controller.py`), `Patch.on_evolve(index)`,
group-resolved sidechain (`SidechainSource.group_name`,
`PatchRackApp._resolve_group_patch` in `src/flet/base.py`) and the rack `MacroSpec`
all shipped without dedicated tests. This is the only outstanding item from the
rack-linking work.

Use `uv run pytest` and `uv run ruff check src`. Follow the style in
`tests/test_deep_house_patches.py` / `tests/test_flet_patch_groups.py`.

## Tests to add

- A `GroupController` fires `on_evolve` at the right bar boundary and not before.
- The resolved patch is whichever instance is currently active in the group, including after a mid-run swap.
- `_stop_engine` tears the controller down (no further fires after stop).
- `Keys.on_evolve` wraps its index, and `next_step()` reads the new progression on the next bar boundary, not the tick it fired on.
- Sidechain duck rests at 1.0 with the kick off.
- Sidechain duck follows an active-kick-variant swap.
- The lofi `_apply_energy` macro at 0.0 / 1.0 for both `lead` styles (currently only verified by hand).

## Open questions

- Should `on_evolve` periods be user-adjustable per group (`GroupController.set_bars` already supports it), or stay fixed in the rack module? Start fixed.
- Should sidechain depth/release be sliders or fixed constants? Start fixed; promote only if one value doesn't sit right across kick variants.
- Smoke-test the lofi Energy slider in the Flet app (`uv run flet run src/flet/lofi/app.py`); no audio backend was available when it landed.
- `noise` in the lofi rack has no `on_evolve`. Its styles are behaviour hooks, not data variants, so it needs a "rotate parameter presets" shape designed first.
