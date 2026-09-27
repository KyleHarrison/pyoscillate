# Run: uv run flet run src/flet/psyambient/app.py

from pathlib import Path

import flet as ft
from pyoscillate.projects.psyambient.rack import PsyambientRack
from src.flet.base import PatchRackApp


def main(page: ft.Page) -> None:
    PatchRackApp(
        page,
        "Psyambient",
        "Ambient rack",
        PsyambientRack(),
        catalog_dir=Path(__file__).parent / "presets",
    )


if __name__ == "__main__":
    ft.run(main)
