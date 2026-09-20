# Run: uv run flet run src/flet/deep_house/app.py

from pathlib import Path

import flet as ft
from pyoscillate.projects.deep_house.rack import PATCH_GROUPS
from src.flet.base import EngineSpec, PatchRackApp


def main(page: ft.Page) -> None:
    PatchRackApp(
        page,
        "Deep House Rack",
        "15 original, clock-locked voices",
        PATCH_GROUPS,
        EngineSpec(nchnls=2, bpm=122, needs_clock=True),
        catalog_dir=Path(__file__).parent / "presets",
    )


if __name__ == "__main__":
    ft.run(main)
