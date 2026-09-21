# Run: uv run flet run src/flet/rack_demo/app.py

from pathlib import Path

import flet as ft
from pyoscillate.projects.rack_demo.rack import BPM, PATCH_GROUPS
from src.flet.base import EngineSpec, PatchRackApp


def main(page: ft.Page) -> None:
    PatchRackApp(
        page,
        "Rack Demo",
        "Groove rack",
        PATCH_GROUPS,
        EngineSpec(nchnls=2, bpm=BPM, needs_clock=True),
        catalog_dir=Path(__file__).parent / "presets",
    )


if __name__ == "__main__":
    ft.run(main)
