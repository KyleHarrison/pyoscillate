# Run: uv run flet run src/flet/rack_demo/app.py

from pathlib import Path

import flet as ft
from pyoscillate.projects.rack_demo.rack import RackDemoRack
from src.flet.base import PatchRackApp


def main(page: ft.Page) -> None:
    PatchRackApp(
        page,
        "Rack Demo",
        "Groove rack",
        RackDemoRack(),
        catalog_dir=Path(__file__).parent / "presets",
    )


if __name__ == "__main__":
    ft.run(main)
