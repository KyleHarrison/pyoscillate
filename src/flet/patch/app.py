# Run: uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.bass.funk.funk
#      uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.bass.groove
"""Play any single patch module in the rack GUI, without a project rack.

The module's `Patch` subclass is declared as a `Slot` in a one-group
`SinglePatchRack`: `name`/`title`/`summary`/`params` all come from the
patch itself, same as a project rack. When a
module defines several style variants (e.g. `kick.py`'s `KickRound` /
`KickPunch` / `KickSoft`), pass `style=<name fragment>` to pick one by a
case-insensitive match against its class name to choose the starting style.
A module with several styles shows a "Style" dropdown that swaps the patch
live (audio server and clock keep running); `style` is optional.

Any other `key=value` arguments after the module path are converted with
`float()` and fixed into the instance's initial parameter values, for the
non-slider choices a rack would otherwise bake in. Selecting the module and
style from command-line strings is this dev harness's one external boundary;
the rack itself is fully typed.
"""

import importlib
import inspect
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import flet as ft
from pyoscillate.controller import GroupController, Slot
from pyoscillate.patches.base import Patch
from pyoscillate.projects.base import Rack
from src.flet.base import PatchRackApp


class SinglePatchRack(Rack):
    """A rack of one patch, whose class and starting values come from the CLI
    args - this dev harness has no project-level `rack.py` to subclass `Rack`
    from. `for_patch()` builds the rack class declaratively: one `Slot` in one
    `GroupController`."""

    bpm = 120

    @classmethod
    def for_patch(
        cls, patch_class: type[Patch], values: dict[str, float]
    ) -> type[Rack]:
        slot = Slot(patch_class, **values)
        group = GroupController(patch_class.title, (slot,), patch_class.summary)
        return type(cls.__name__, (cls,), {"patch_slot": slot, "patch_group": group})


def _patch_classes(module: ModuleType) -> dict[str, type[Patch]]:
    """The concrete, most-specific `Patch` subclasses defined directly in
    `module` - excluding any class that's a shared base for another
    candidate in the same module (e.g. `kick.py`'s `Kick`), since those
    describe a style family rather than a playable voice on their own."""
    candidates = {
        name: obj
        for name, obj in vars(module).items()
        if inspect.isclass(obj)
        and issubclass(obj, Patch)
        and obj.__module__ == module.__name__
        and not inspect.isabstract(obj)
    }
    bases = {ancestor for obj in candidates.values() for ancestor in obj.__mro__[1:]}
    return {name: obj for name, obj in candidates.items() if obj not in bases}


def _select_class(module: ModuleType, style: str | None) -> type[Patch]:
    classes = _patch_classes(module)
    if not classes:
        raise SystemExit(f"{module.__name__} defines no playable Patch subclass")
    if style is None:
        if len(classes) == 1:
            return next(iter(classes.values()))
        return next(iter(classes.values()))

    def squash(text: str) -> str:
        return "".join(ch for ch in text.lower() if ch.isalnum())

    matches = [cls for name, cls in classes.items() if squash(style) in squash(name)]
    if len(matches) != 1:
        raise SystemExit(
            f"style={style!r} matched {len(matches)} patches in {module.__name__} - available: "
            + ", ".join(sorted(classes))
        )
    return matches[0]


def _variant(
    patch_class: type[Patch], values: dict[str, float]
) -> Callable[[], tuple[Rack, Path]]:
    return lambda: (
        SinglePatchRack.for_patch(patch_class, values)(),
        Path(__file__).parent / "presets" / patch_class.name,
    )


def main(page: ft.Page) -> None:
    module = importlib.import_module(sys.argv[1])
    fixed = dict(arg.split("=", 1) for arg in sys.argv[2:])
    style = fixed.pop("style", None)
    values = {key: float(value) for key, value in fixed.items()}
    classes = _patch_classes(module)
    patch_class = _select_class(module, style)
    # a multi-style module gets a live style dropdown; `style=` only picks the
    # starting one
    variants = (
        {name: _variant(cls, values) for name, cls in classes.items()}
        if len(classes) > 1
        else None
    )
    variant = next((n for n, c in classes.items() if c is patch_class), None)

    rack, catalog_dir = _variant(patch_class, values)()
    PatchRackApp(
        page,
        patch_class.title,
        patch_class.summary,
        rack,
        catalog_dir=catalog_dir,
        variants=variants,
        variant=variant,
    )


if __name__ == "__main__":
    ft.run(main)
