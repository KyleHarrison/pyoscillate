# Run: uv run flet run src/flet/deep_house/app.py

from pathlib import Path

import flet as ft
from pyoscillate.projects.deep_house.rack import PATCH_DEFS
from src.flet.base import EngineSpec, PatchRackApp

CATALOG_DIR = Path(__file__).parent.parent / "presets" / "deep_house"


def main(page: ft.Page) -> None:
    PatchRackApp(
        page,
        "Deep House Rack",
        "15 original, clock-locked voices",
        CATALOG_DIR,
        PATCH_DEFS,
        EngineSpec(nchnls=2, bpm=122, needs_clock=True),
    )
