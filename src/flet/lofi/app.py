# Run: uv run flet run src/flet/lofi/app.py

from pathlib import Path

import flet as ft
from pyoscillate.projects.lofi.rack import LofiRack
from src.flet.base import PatchRackApp


def main(page: ft.Page) -> None:
    PatchRackApp(
        page,
        "Lofi Rack",
        "Dusty keys, muted bass, soft boom-bap drums",
        LofiRack(),
        catalog_dir=Path(__file__).parent / "presets",
    )


if __name__ == "__main__":
    ft.run(main)
