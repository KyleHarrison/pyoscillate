# Run: uv run flet run src/flet/slowed_reverb/app.py

from pathlib import Path

import flet as ft
from pyoscillate.projects.lofi.slowed_reverb.rack import SlowedReverbRack
from src.flet.base import PatchRackApp


def main(page: ft.Page) -> None:
    PatchRackApp(
        page,
        "Slowed Reverb",
        "Dark, hovering bass under a long, breathing reverb tail",
        SlowedReverbRack(),
        catalog_dir=Path(__file__).parent / "presets",
    )


if __name__ == "__main__":
    ft.run(main)
