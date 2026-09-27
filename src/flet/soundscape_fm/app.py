# Run: uv run flet run src/flet/soundscape_fm/app.py

from pathlib import Path

import flet as ft
from pyoscillate.projects.soundscape_fm.rack import SoundscapeFmRack
from src.flet.base import PatchRackApp


def main(page: ft.Page) -> None:
    PatchRackApp(
        page,
        "FM Soundscape",
        "Chaotic drift",
        SoundscapeFmRack(),
        catalog_dir=Path(__file__).parent / "presets",
    )


if __name__ == "__main__":
    ft.run(main)
