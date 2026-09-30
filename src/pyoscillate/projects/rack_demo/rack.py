"""Patch definitions for the clock-locked groove demo."""

from pyoscillate.controller import GroupController, Slot
from pyoscillate.patches.drums import hat, low_hat
from pyoscillate.patches.musical.clock_tick import ClockTick
from pyoscillate.patches.texture.atmosphere import Atmosphere
from pyoscillate.patches.tonal.bass import TechnoBass
from pyoscillate.patches.tonal.drone import Drone
from pyoscillate.projects.base import Rack


class RackDemoRack(Rack):
    """The clock-locked groove demo."""

    # this project's own tempo - other projects set their own value instead of
    # sharing one hardcoded in app.py
    bpm = 132

    rhythm_group = GroupController(
        "Rhythm", (Slot(TechnoBass), Slot(hat.Tick), Slot(low_hat.LowHat))
    )
    atmosphere_group = GroupController("Atmosphere", (Slot(Atmosphere), Slot(Drone)))
    utility_group = GroupController("Utility", (Slot(ClockTick),))
