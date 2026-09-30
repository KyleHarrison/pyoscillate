"""Patch definitions for the standalone FM soundscape."""

from pyoscillate.controller import GroupController, Slot
from pyoscillate.patches.tonal.drone.fm import SoundscapeFm
from pyoscillate.projects.base import Rack


class SoundscapeFmRack(Rack):
    """The standalone FM soundscape."""

    bpm = 60

    soundscapes_group = GroupController("Soundscapes", (Slot(SoundscapeFm),))
