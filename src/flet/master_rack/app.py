# Run: uv run flet run src/flet/master_rack/app.py

from pathlib import Path

import flet as ft
from pyoscillate.projects.master_rack.rack import MasterRack
from src.flet.base import PatchRackApp


def main(page: ft.Page) -> None:
    PatchRackApp(
        page,
        "Master Rack",
        "Every patch, grouped by category - add what you want to hear",
        MasterRack(),
        catalog_dir=Path(__file__).parent / "presets",
    )


if __name__ == "__main__":
    ft.run(main)
