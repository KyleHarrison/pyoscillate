# Run: uv run flet run src/flet/deep_house/app.py

from pathlib import Path

import flet as ft
from pyoscillate.projects.deep_house.rack import DeepHouseRack
from src.flet.base import PatchRackApp


def main(page: ft.Page) -> None:
    PatchRackApp(
        page,
        "Deep House Rack",
        "15 original, clock-locked voices",
        DeepHouseRack(),
        catalog_dir=Path(__file__).parent / "presets",
    )


if __name__ == "__main__":
    ft.run(main)
