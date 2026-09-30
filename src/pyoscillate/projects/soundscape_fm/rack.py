"""Patch definitions for the standalone FM soundscape."""

from functools import partial

from pyoscillate.controller import GroupController
from pyoscillate.patches.tonal.drone.fm import SoundscapeFm
from pyoscillate.projects.base import Rack


class SoundscapeFmRack(Rack):
    """The standalone FM soundscape."""

    soundscapes = GroupController(
        "soundscapes",
        "Soundscapes",
        (partial(SoundscapeFm, title="Soundscape FM"),),
    )
