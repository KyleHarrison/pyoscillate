# Run: uv run flet run src/flet/deep_house/app.py

from pathlib import Path

import flet as ft
from pyoscillate.projects.deep_house.rack import BPM, PATCH_GROUPS, TICKS_PER_BAR
from src.flet.base import EngineSpec, PatchRackApp


def main(page: ft.Page) -> None:
    PatchRackApp(
        page,
        "Deep House Rack",
        "15 original, clock-locked voices",
        PATCH_GROUPS,
        EngineSpec(nchnls=2, bpm=BPM, needs_clock=True, ticks_per_bar=TICKS_PER_BAR),
        catalog_dir=Path(__file__).parent / "presets",
    )


if __name__ == "__main__":
    ft.run(main)
