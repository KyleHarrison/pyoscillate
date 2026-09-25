# Run: uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.bass.funk.funk
#      uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.bass.groove style=rolling
"""Play any single patch module in the rack GUI, without a project rack.

The `PatchDef` is read off the module itself: `build` and `PARAMETERS`, an
optional `VOLUME_DEFAULT`, and the shared objects `build` asks for by name
(`tempo`, `clock`, `harmony`), which decide what the engine starts.

Any `key=value` arguments after the module path are fixed into `build`, for
the non-slider choices a rack would otherwise bake in (a bass or riser
`style`).
"""

import functools
import importlib
import inspect
import sys
from pathlib import Path

import flet as ft
from pyoscillate.harmony import Harmony
from src.flet.base import EngineSpec, PatchDef, PatchGroupDef, PatchRackApp

BPM = 120
INJECTED = ("tempo", "clock", "harmony")


def main(page: ft.Page) -> None:
    module = importlib.import_module(sys.argv[1])
    fixed = dict(arg.split("=", 1) for arg in sys.argv[2:])
    wants = inspect.signature(module.build).parameters
    sliders = {spec.name for spec in module.PARAMETERS}
    missing = [
        param.name
        for param in wants.values()
        if param.default is inspect.Parameter.empty
        and param.name not in (*INJECTED, *sliders, *fixed)
    ]
    if missing:
        raise SystemExit(f"{module.__name__}.build needs {', '.join(f'{m}=...' for m in missing)}")

    name = "_".join([module.__name__.rsplit(".", 1)[-1], *fixed.values()])
    summary = (module.__doc__ or "").strip().split("\n")[0]
    needs_tempo = "tempo" in wants or "clock" in wants

    patch_def = PatchDef(
        name=name,
        title=name.replace("_", " ").title(),
        summary=summary,
        build=functools.partial(module.build, **fixed),
        parameters=module.PARAMETERS,
        volume_default=getattr(module, "VOLUME_DEFAULT", 0.6),
        needs_tempo=needs_tempo,
        needs_clock="clock" in wants,
        needs_harmony="harmony" in wants,
    )
    PatchRackApp(
        page,
        patch_def.title,
        summary,
        [PatchGroupDef(name, patch_def.title, (patch_def,))],
        EngineSpec(
            nchnls=2,
            bpm=BPM if needs_tempo else None,
            needs_clock=patch_def.needs_clock,
            harmony=Harmony() if patch_def.needs_harmony else None,
        ),
        catalog_dir=Path(__file__).parent / "presets" / name,
    )


if __name__ == "__main__":
    ft.run(main)
