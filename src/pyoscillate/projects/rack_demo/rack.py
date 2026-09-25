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

PATCH_DEFS: list[PatchDef] = [
    PatchDef(TechnoBass()),
    PatchDef(Atmosphere()),
    PatchDef(hat.Tick()),
    PatchDef(low_hat.LowHat()),
    PatchDef(ClockTick()),
    PatchDef(Drone()),
]

PATCH_GROUPS: list[PatchGroupDef] = [
    PatchGroupDef("rhythm", "Rhythm", (PATCH_DEFS[0], PATCH_DEFS[2], PATCH_DEFS[3])),
    PatchGroupDef("atmosphere", "Atmosphere", (PATCH_DEFS[1], PATCH_DEFS[5])),
    PatchGroupDef("utility", "Utility", (PATCH_DEFS[4],)),
]
