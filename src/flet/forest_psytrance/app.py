# Run: uv run flet run src/flet/forest_psytrance/app.py

from pathlib import Path

import flet as ft
from pyoscillate.projects.forest_psytrance.rack import ForestPsytranceRack
from src.flet.base import PatchRackApp


def main(page: ft.Page) -> None:
    PatchRackApp(
        page,
        "Forest Psytrance",
        "160 BPM rolling bass, subtle hats, windy FM leads",
        ForestPsytranceRack(),
        catalog_dir=Path(__file__).parent / "presets",
    )


if __name__ == "__main__":
    ft.run(main)
