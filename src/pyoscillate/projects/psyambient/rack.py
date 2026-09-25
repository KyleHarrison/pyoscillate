"""Patch definitions for the free-running psyambient rack."""

from pyoscillate.patches.musical.arp.arp import Arp
from pyoscillate.patches.musical.canon.canon import Canon
from pyoscillate.patches.musical.generative.generative import Generative
from pyoscillate.patches.texture.rumble.rumble import BassRumble
from pyoscillate.patches.tonal.drone.filter import SoundscapeFilter
from pyoscillate.patches.tonal.drone.fm import SoundscapeFm
from pyoscillate.patches.tonal.drone.sub_chaos import BassChaos
from pyoscillate.patches.tonal.drone.sub_swell import BassDrone
from pyoscillate.patches.tonal.drone.wash import SoundscapeWash
from src.flet.base import PatchDef, PatchGroupDef

# this project's own tempo - other projects set their own value instead of
# sharing one hardcoded in app.py
BPM = 70

PATCH_DEFS: list[PatchDef] = [
    PatchDef(SoundscapeFm()),
    PatchDef(SoundscapeFilter()),
    PatchDef(SoundscapeWash()),
    PatchDef(Arp()),
    PatchDef(Generative()),
    PatchDef(Canon()),
    PatchDef(BassDrone()),
    PatchDef(BassChaos()),
    PatchDef(BassRumble()),
]

PATCH_GROUPS: list[PatchGroupDef] = [
    PatchGroupDef(
        "soundscapes",
        "Soundscapes",
        tuple(PATCH_DEFS[0:3]),
        "Choose and combine evolving atmospheric beds.",
    ),
    PatchGroupDef(
        "mid",
        "Mid Voices",
        tuple(PATCH_DEFS[3:6]),
        "Melodic movement in the center of the arrangement.",
    ),
    PatchGroupDef(
        "bass",
        "Bass",
        tuple(PATCH_DEFS[6:9]),
        "Low-frequency foundations and textures.",
    ),
]
