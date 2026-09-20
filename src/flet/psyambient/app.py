# Run: uv run flet run src/flet/psyambient/app.py

from pathlib import Path

import flet as ft
from pyoscillate.projects.psyambient.rack import PATCH_DEFS
from src.flet.base import EngineSpec, PatchRackApp

CATALOG_DIR = Path(__file__).parent.parent / "presets" / "psyambient"


def main(page: ft.Page) -> None:
    PatchRackApp(
        page,
        "Psyambient",
        "Ambient rack",
        CATALOG_DIR,
        PATCH_DEFS,
        EngineSpec(nchnls=2, bpm=70, needs_clock=True),
    )
