"""Flet port of `notebooks/rack_demo/rack_demo.ipynb`.

Six clock-locked groove patches from `pyoscillate.patches` (bass, atmosphere,
hat, low_hat, clock_tick, drone), composed onto one shared `PatchRack` via
`src.flet.base.PatchRackApp`. All of them share the same tempo grid; every
patch but `clock_tick` also subscribes to the shared clock.
"""

from __future__ import annotations

from pathlib import Path

import flet as ft
from pyoscillate.patches import atmosphere, bass, clock_tick, drone, hat, low_hat
from src.flet.base import EngineSpec, PatchDef, PatchRackApp

CATALOG_DIR = Path(__file__).parent / "presets" / "rack_demo"

PATCH_DEFS = [
    PatchDef(
        name="bass",
        title="Bass",
        summary="Rolling 16-step bassline through a resonant, LFO-swept lowpass filter.",
        build=bass.build,
        parameters=bass.PARAMETERS,
        volume_default=1.0,
        needs_tempo=True,
        needs_clock=True,
    ),
    PatchDef(
        name="atmosphere",
        title="Atmosphere (FM pad + arpeggiator)",
        summary="FM pad voice arpeggiated at 8th notes, with a slow amplitude swell and reverb.",
        build=atmosphere.build,
        parameters=atmosphere.PARAMETERS,
        volume_default=0.6,
        rebuild_parameters=("step_division",),
        needs_tempo=True,
        needs_clock=True,
    ),
    PatchDef(
        name="hat",
        title="Hi-hat",
        summary="Subtle high-passed noise tick, once per 8th note.",
        build=hat.build,
        parameters=hat.PARAMETERS,
        volume_default=0.2,
        rebuild_parameters=("decay",),
        needs_tempo=True,
        needs_clock=True,
    ),
    PatchDef(
        name="low_hat",
        title="Low hat",
        summary="Darker noise tick, once per quarter note, as a rarer accent.",
        build=low_hat.build,
        parameters=low_hat.PARAMETERS,
        volume_default=0.2,
        rebuild_parameters=("decay",),
        needs_tempo=True,
        needs_clock=True,
    ),
    PatchDef(
        name="clock_tick",
        title="Clock tick",
        summary="Pink Floyd 'Time'-style clock shop: four free-running noise ticks.",
        build=clock_tick.build,
        parameters=clock_tick.PARAMETERS,
        volume_default=1.0,
        needs_tempo=True,
    ),
    PatchDef(
        name="drone",
        title="Drone",
        summary="Slow-winding FM drone: note changes once every 8 bars.",
        build=drone.build,
        parameters=drone.PARAMETERS,
        volume_default=1.0,
        needs_tempo=True,
        needs_clock=True,
    ),
]


def main(page: ft.Page) -> None:
    PatchRackApp(
        page=page,
        title="Rack Demo",
        subtitle="Groove rack",
        catalog_dir=CATALOG_DIR,
        patch_defs=PATCH_DEFS,
        engine=EngineSpec(nchnls=2, bpm=132, needs_clock=True),
    )


if __name__ == "__main__":
    ft.run(main)
