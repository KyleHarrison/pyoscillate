# Run: uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.bass.funk.funk
#      uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.bass.groove style=rolling
"""Play any single patch module in the rack GUI, without a project rack.

The module's `Patch` subclass is instantiated directly and dropped into a
`GroupController` of one: `name`/`title`/`summary`/`params` all come from the
patch itself, same as a project rack. When a
module defines several style variants (e.g. `kick.py`'s `KickRound` /
`KickPunch` / `KickSoft`), pass `style=<name fragment>` to pick one by a
case-insensitive match against its class name; with only one concrete
`Patch` subclass in the module, `style` is optional.

Any other `key=value` arguments after the module path are converted with
`float()` and fixed into the instance's initial parameter values, for the
non-slider choices a rack would otherwise bake in. Selecting the module and
style from command-line strings is this dev harness's one external boundary;
the rack itself is fully typed.
"""

import importlib
import inspect
import sys
from pathlib import Path
from types import ModuleType

import flet as ft
from pyoscillate.controller import GroupController
from pyoscillate.patches.base import Patch
from pyoscillate.projects.base import Rack
from src.flet.base import PatchRackApp


class SinglePatchRack(Rack):
    """Wraps one `Patch` instance, selected at runtime from the CLI args, in
    the `Rack` interface `PatchRackApp` expects - this dev harness has no
    project-level `rack.py` of its own to subclass `Rack` from."""

    bpm = 120

    patch: Patch

    def __init__(self, patch: Patch) -> None:
        # assigned before `super().__init__()`, which calls `build_groups()`
        self.patch = patch
        super().__init__()

    def build_groups(self) -> tuple[GroupController, ...]:
        return (GroupController(self.patch.title, (self.patch,), self.patch.summary),)


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
        raise SystemExit(
            f"{module.__name__} defines several patches - pass style=<name>, one of: "
            + ", ".join(sorted(classes))
        )
    matches = [cls for name, cls in classes.items() if style.lower() in name.lower()]
    if len(matches) != 1:
        raise SystemExit(
            f"style={style!r} matched {len(matches)} patches in {module.__name__} - available: "
            + ", ".join(sorted(classes))
        )
    return matches[0]


def main(page: ft.Page) -> None:
    module = importlib.import_module(sys.argv[1])
    fixed = dict(arg.split("=", 1) for arg in sys.argv[2:])
    style = fixed.pop("style", None)
    patch = _select_class(module, style)(
        **{key: float(value) for key, value in fixed.items()}
    )

    PatchRackApp(
        page,
        patch.title,
        patch.summary,
        SinglePatchRack(patch),
        catalog_dir=Path(__file__).parent / "presets" / patch.name,
    )


if __name__ == "__main__":
    ft.run(main)
