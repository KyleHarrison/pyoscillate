"""Patch definitions for the standalone FM soundscape."""

from pyoscillate.patches.psyambient import soundscape_fm
from src.flet.base import PatchDef

PATCH_DEFS: list[PatchDef] = [
    PatchDef(
        name="soundscape_fm",
        title="Soundscape FM",
        summary="Chaotic FM pad driven by Rossler/Lorenz attractors.",
        build=soundscape_fm.build,
        parameters=soundscape_fm.PARAMETERS,
        volume_default=0.6,
    )
]
