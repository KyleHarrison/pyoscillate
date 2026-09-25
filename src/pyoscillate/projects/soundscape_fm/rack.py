"""Patch definitions for the standalone FM soundscape."""

from pyoscillate.patches.base import FunctionVoice
from pyoscillate.patches.tonal.drone import fm as soundscape_fm
from src.flet.base import PatchDef, PatchGroupDef

PATCH_DEFS: list[PatchDef] = [
    PatchDef(
        FunctionVoice.from_module(soundscape_fm, volume_default=0.6),
        name="soundscape_fm",
        title="Soundscape FM",
        summary="Slow-morphing, unpredictable pad that never quite repeats itself.",
    )
]

PATCH_GROUPS: list[PatchGroupDef] = [PatchGroupDef("soundscapes", "Soundscapes", tuple(PATCH_DEFS))]
