"""Patch definitions for the standalone FM soundscape."""

from pyoscillate.patches.tonal.drone.fm import SoundscapeFm
from pyoscillate.projects.base import Rack
from src.flet.base import PatchGroupDef


class SoundscapeFmRack(Rack):
    """The standalone FM soundscape."""

    def build_groups(self) -> tuple[PatchGroupDef, ...]:
        return (
            PatchGroupDef(
                "soundscapes", "Soundscapes", (SoundscapeFm(title="Soundscape FM"),)
            ),
        )
