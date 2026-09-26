# Run: uv run flet run src/flet/lofi/app.py

from pathlib import Path

import flet as ft
from pyoscillate.projects.lofi.rack import (
    BPM,
    HARMONY,
    PATCH_GROUPS,
    TICKS_PER_BAR,
)
from src.flet.base import EngineSpec, PatchRackApp


def main(page: ft.Page) -> None:
    PatchRackApp(
        page,
        "Lofi Rack",
        "Dusty keys, muted bass, soft boom-bap drums",
        PATCH_GROUPS,
        EngineSpec(
            nchnls=2,
            bpm=BPM,
            needs_clock=True,
            ticks_per_bar=TICKS_PER_BAR,
            harmony=HARMONY,
        ),
        catalog_dir=Path(__file__).parent / "presets",
    )


if __name__ == "__main__":
    ft.run(main)
