# Run: uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.bass.funk.funk
#      uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.bass.groove style=rolling
"""Play any single patch module in the rack GUI, without a project rack.

The module's `Patch` subclass is instantiated directly and dropped into a
`PatchGroupDef` of one: `name`/`title`/`summary`/`parameters`/`volume_default`/
`needs_*` all come from the instance itself, same as a project rack. When a
module defines several style variants (e.g. `kick.py`'s `KickRound` /
`KickPunch` / `KickSoft`), pass `style=<name fragment>` to pick one by a
case-insensitive match against its class name; with only one concrete
`Patch` subclass in the module, `style` is optional.

Any other `key=value` arguments after the module path are fixed into the
instance's initial parameter values, for the non-slider choices a rack would
otherwise bake in.
"""

import importlib
import inspect
import sys
from pathlib import Path
from types import ModuleType

import flet as ft
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import Patch
from pyoscillate.projects.base import Rack
from src.flet.base import PatchGroupDef, PatchRackApp

BPM = 120


class SinglePatchRack(Rack):
    """Wraps one `Patch` instance, selected at runtime from the CLI args, in
    the `Rack` interface `PatchRackApp` expects - this dev harness has no
    project-level `rack.py` of its own to subclass `Rack` from."""

    def __init__(self, patch: Patch) -> None:
        self.patch = patch
        needs_tempo = patch.needs_tempo or patch.needs_clock
        self.bpm = BPM if needs_tempo else None
        self.needs_clock = patch.needs_clock
        self.harmony = Harmony() if patch.needs_harmony else None

    def build_groups(self) -> tuple[PatchGroupDef, ...]:
        return (PatchGroupDef(self.patch.name, self.patch.title, (self.patch,)),)


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
    patch = _select_class(module, style)(**fixed)

    PatchRackApp(
        page,
        patch.title,
        patch.summary,
        SinglePatchRack(patch),
        catalog_dir=Path(__file__).parent / "presets" / patch.name,
    )


if __name__ == "__main__":
    ft.run(main)
