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

PATCH_DEFS: dict[str, tuple[PatchDef, ...]] = {
    "soundscapes": (
        PatchDef(SoundscapeFm()),
        PatchDef(SoundscapeFilter()),
        PatchDef(SoundscapeWash()),
    ),
    "mid": (
        PatchDef(Arp()),
        PatchDef(Generative()),
        PatchDef(Canon()),
    ),
    "bass": (
        PatchDef(BassDrone()),
        PatchDef(BassChaos()),
        PatchDef(BassRumble()),
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
    PatchGroupDef(key, GROUP_TITLES[key], defs, GROUP_SUMMARIES[key])
    for key, defs in PATCH_DEFS.items()
]
