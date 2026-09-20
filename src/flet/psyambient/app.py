# Run: uv run flet run src/flet/psyambient/app.py

from pathlib import Path

import flet as ft
from pyoscillate.projects.psyambient.rack import PATCH_GROUPS
from src.flet.base import EngineSpec, PatchRackApp


def main(page: ft.Page) -> None:
    PatchRackApp(
        page,
        "Psyambient",
        "Ambient rack",
        PATCH_GROUPS,
        EngineSpec(nchnls=2, bpm=70, needs_clock=True),
        catalog_dir=Path(__file__).parent / "presets",
    )


if __name__ == "__main__":
    ft.run(main)
