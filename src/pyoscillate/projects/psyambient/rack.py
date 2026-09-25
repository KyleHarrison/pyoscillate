"""Patch definitions for the free-running psyambient rack."""

from pyoscillate.patches.base import Patch
from pyoscillate.patches.musical.arp.arp import Arp
from pyoscillate.patches.musical.canon.canon import Canon
from pyoscillate.patches.musical.generative.generative import Generative
from pyoscillate.patches.texture.rumble.rumble import BassRumble
from pyoscillate.patches.tonal.drone.filter import SoundscapeFilter
from pyoscillate.patches.tonal.drone.fm import SoundscapeFm
from pyoscillate.patches.tonal.drone.sub_chaos import BassChaos
from pyoscillate.patches.tonal.drone.sub_swell import BassDrone
from pyoscillate.patches.tonal.drone.wash import SoundscapeWash
from src.flet.base import PatchGroupDef

# this project's own tempo - other projects set their own value instead of
# sharing one hardcoded in app.py
BPM = 70

PATCHES: dict[str, tuple[Patch, ...]] = {
    "soundscapes": (
        SoundscapeFm(),
        SoundscapeFilter(),
        SoundscapeWash(),
    ),
    "mid": (
        Arp(),
        Generative(),
        Canon(),
    ),
    "bass": (
        BassDrone(),
        BassChaos(),
        BassRumble(),
    ),
}

GROUP_TITLES: dict[str, str] = {
    "soundscapes": "Soundscapes",
    "mid": "Mid Voices",
    "bass": "Bass",
}

GROUP_SUMMARIES: dict[str, str] = {
    "soundscapes": "Choose and combine evolving atmospheric beds.",
    "mid": "Melodic movement in the center of the arrangement.",
    "bass": "Low-frequency foundations and textures.",
}

PATCH_GROUPS: list[PatchGroupDef] = [
    PatchGroupDef(key, GROUP_TITLES[key], patches, GROUP_SUMMARIES[key])
    for key, patches in PATCHES.items()
]
