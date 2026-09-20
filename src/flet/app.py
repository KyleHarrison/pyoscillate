from __future__ import annotations

from pathlib import Path

import flet as ft
from pyoscillate.patches.psyambient import soundscape_fm
from src.flet.base import EngineSpec, PatchDef, PatchRackApp

CATALOG_DIR = Path(__file__).parent / "presets" / "soundscape_fm"


def main(page: ft.Page) -> None:
    patch_def = PatchDef(
        name="soundscape_fm",
        title="Soundscape FM",
        summary="Chaotic FM pad driven by Rossler/Lorenz attractors.",
        build=soundscape_fm.build,
        parameters=soundscape_fm.PARAMETERS,
        volume_default=0.6,
    )
    PatchRackApp(
        page=page,
        title="FM Soundscape",
        subtitle="Chaotic drift",
        catalog_dir=CATALOG_DIR,
        patch_defs=[patch_def],
        engine=EngineSpec(nchnls=2),
    )


if __name__ == "__main__":
    ft.run(main)
