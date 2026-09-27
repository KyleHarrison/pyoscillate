"""Patch definitions for the free-running psyambient rack."""

from pyoscillate.controller import GroupController
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
    needs_clock = True

    def build_groups(self) -> tuple[GroupController, ...]:
        return (
            GroupController(
                "soundscapes",
                "Soundscapes",
                (SoundscapeFm(), SoundscapeFilter(), SoundscapeWash()),
                "Choose and combine evolving atmospheric beds.",
            ),
            GroupController(
                "mid",
                "Mid Voices",
                (Arp(), Generative(), Canon()),
                "Melodic movement in the center of the arrangement.",
            ),
            GroupController(
                "bass",
                "Bass",
                (BassDrone(), BassChaos(), BassRumble()),
                "Low-frequency foundations and textures.",
            ),
        )
