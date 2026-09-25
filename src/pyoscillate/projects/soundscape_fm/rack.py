"""Patch definitions for the standalone FM soundscape."""

from pyoscillate.patches.base import Patch
from pyoscillate.patches.tonal.drone.fm import SoundscapeFm
from src.flet.base import PatchGroupDef

PATCHES: dict[str, tuple[Patch, ...]] = {
    "soundscapes": (SoundscapeFm(title="Soundscape FM"),),
}

PATCH_GROUPS: list[PatchGroupDef] = [
    PatchGroupDef("soundscapes", "Soundscapes", PATCHES["soundscapes"])
]
