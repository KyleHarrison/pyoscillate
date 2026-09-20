# Run: uv run flet run src/flet/rack_demo/app.py

from pathlib import Path

import flet as ft
from pyoscillate.projects.rack_demo.rack import PATCH_DEFS
from src.flet.base import EngineSpec, PatchRackApp

CATALOG_DIR = Path(__file__).parent.parent / "presets" / "rack_demo"


def main(page: ft.Page) -> None:
    PatchRackApp(
        page,
        "Rack Demo",
        "Groove rack",
        CATALOG_DIR,
        PATCH_DEFS,
        EngineSpec(nchnls=2, bpm=132, needs_clock=True),
    )
