"""Patch definitions for the standalone FM soundscape."""

from pyoscillate.controller import GroupController
from pyoscillate.patches.tonal.drone.fm import SoundscapeFm
from pyoscillate.projects.base import Rack


class SoundscapeFmRack(Rack):
    """The standalone FM soundscape."""

    def build_groups(self) -> tuple[GroupController, ...]:
        return (
            GroupController(
                "soundscapes", "Soundscapes", (SoundscapeFm(title="Soundscape FM"),)
            ),
        )
