"""Patch definitions for the clock-locked groove demo."""

from pyoscillate.patches.base import Patch
from pyoscillate.patches.drums import hat, low_hat
from pyoscillate.patches.musical.clock_tick import ClockTick
from pyoscillate.patches.texture.atmosphere import Atmosphere
from pyoscillate.patches.tonal.bass import TechnoBass
from pyoscillate.patches.tonal.drone import Drone
from src.flet.base import PatchGroupDef

# this project's own tempo - other projects set their own value instead of
# sharing one hardcoded in app.py
BPM = 132

PATCHES: dict[str, tuple[Patch, ...]] = {
    "rhythm": (
        TechnoBass(),
        hat.Tick(),
        low_hat.LowHat(),
    ),
    "atmosphere": (
        Atmosphere(),
        Drone(),
    ),
    "utility": (ClockTick(),),
}

GROUP_TITLES: dict[str, str] = {
    "rhythm": "Rhythm",
    "atmosphere": "Atmosphere",
    "utility": "Utility",
}

PATCH_GROUPS: list[PatchGroupDef] = [
    PatchGroupDef(key, GROUP_TITLES[key], patches) for key, patches in PATCHES.items()
]
