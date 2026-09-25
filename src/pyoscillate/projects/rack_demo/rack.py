"""Patch definitions for the clock-locked groove demo."""

from pyoscillate.patches.drums import hat, low_hat
from pyoscillate.patches.musical.clock_tick import ClockTick
from pyoscillate.patches.texture.atmosphere import Atmosphere
from pyoscillate.patches.tonal.bass import TechnoBass
from pyoscillate.patches.tonal.drone import Drone
from src.flet.base import PatchDef, PatchGroupDef

# this project's own tempo - other projects set their own value instead of
# sharing one hardcoded in app.py
BPM = 132

PATCH_DEFS: dict[str, tuple[PatchDef, ...]] = {
    "rhythm": (
        PatchDef(TechnoBass()),
        PatchDef(hat.Tick()),
        PatchDef(low_hat.LowHat()),
    ),
    "atmosphere": (
        PatchDef(Atmosphere()),
        PatchDef(Drone()),
    ),
    "utility": (PatchDef(ClockTick()),),
}

GROUP_TITLES: dict[str, str] = {
    "rhythm": "Rhythm",
    "atmosphere": "Atmosphere",
    "utility": "Utility",
}

PATCH_GROUPS: list[PatchGroupDef] = [
    PatchGroupDef(key, GROUP_TITLES[key], defs) for key, defs in PATCH_DEFS.items()
]
