# Run: uv run flet run src/flet/dubstep/app.py

from pathlib import Path

import flet as ft
from pyoscillate.projects.dubstep.rack import DubstepRack
from src.flet.base import PatchRackApp


def main(page: ft.Page) -> None:
    PatchRackApp(
        page,
        "Dubstep Rack",
        "10 original, clock-locked voices",
        DubstepRack(),
        catalog_dir=Path(__file__).parent / "presets",
    )


if __name__ == "__main__":
    ft.run(main)
