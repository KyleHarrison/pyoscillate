"""Patch definitions for the free-running psyambient rack."""

from pyoscillate.controller import GroupController, Slot
from pyoscillate.patches.musical.arp.arp import Arp
from pyoscillate.patches.musical.canon.canon import Canon
from pyoscillate.patches.musical.generative.generative import Generative
from pyoscillate.patches.texture.rumble.rumble import BassRumble
from pyoscillate.patches.tonal.drone.filter import SoundscapeFilter
from pyoscillate.patches.tonal.drone.fm import SoundscapeFm
from pyoscillate.patches.tonal.drone.sub_chaos import BassChaos
from pyoscillate.patches.tonal.drone.sub_swell import BassDrone
from pyoscillate.patches.tonal.drone.wash import SoundscapeWash
from pyoscillate.projects.base import Rack


class PsyambientRack(Rack):
    """The free-running psyambient rack."""

    # this project's own tempo - other projects set their own value instead of
    # sharing one hardcoded in app.py
    bpm = 70

    soundscapes_group = GroupController(
        "Soundscapes",
        (Slot(SoundscapeFm), Slot(SoundscapeFilter), Slot(SoundscapeWash)),
        "Choose and combine evolving atmospheric beds.",
    )
    mid_group = GroupController(
        "Mid Voices",
        (Slot(Arp), Slot(Generative), Slot(Canon)),
        "Melodic movement in the center of the arrangement.",
    )
    bass_group = GroupController(
        "Bass",
        (Slot(BassDrone), Slot(BassChaos), Slot(BassRumble)),
        "Low-frequency foundations and textures.",
    )
