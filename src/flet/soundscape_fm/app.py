# Run: uv run flet run src/flet/soundscape_fm/app.py

from pathlib import Path

import flet as ft
from pyoscillate.projects.soundscape_fm.rack import PATCH_DEFS
from src.flet.base import EngineSpec, PatchRackApp

CATALOG_DIR = Path(__file__).parent.parent / "presets" / "soundscape_fm"


def main(page: ft.Page) -> None:
    PatchRackApp(
        page, "FM Soundscape", "Chaotic drift", CATALOG_DIR, PATCH_DEFS, EngineSpec(nchnls=2)
    )
