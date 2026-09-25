"""Patch definitions for the standalone FM soundscape."""

from pyoscillate.patches.tonal.drone.fm import SoundscapeFm
from src.flet.base import PatchDef, PatchGroupDef

PATCH_DEFS: dict[str, tuple[PatchDef, ...]] = {
    "soundscapes": (PatchDef(SoundscapeFm(), title="Soundscape FM"),),
}

PATCH_GROUPS: list[PatchGroupDef] = [
    PatchGroupDef("soundscapes", "Soundscapes", PATCH_DEFS["soundscapes"])
]
