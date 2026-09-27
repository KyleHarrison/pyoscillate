"""Patch definitions for the clock-locked groove demo."""

from pyoscillate.patches.drums import hat, low_hat
from pyoscillate.patches.musical.clock_tick import ClockTick
from pyoscillate.patches.texture.atmosphere import Atmosphere
from pyoscillate.patches.tonal.bass import TechnoBass
from pyoscillate.patches.tonal.drone import Drone
from pyoscillate.projects.base import Rack
from src.flet.base import PatchGroupDef


class RackDemoRack(Rack):
    """The clock-locked groove demo."""

    # this project's own tempo - other projects set their own value instead of
    # sharing one hardcoded in app.py
    bpm = 132
    needs_clock = True

    def build_groups(self) -> tuple[PatchGroupDef, ...]:
        return (
            PatchGroupDef(
                "rhythm", "Rhythm", (TechnoBass(), hat.Tick(), low_hat.LowHat())
            ),
            PatchGroupDef("atmosphere", "Atmosphere", (Atmosphere(), Drone())),
            PatchGroupDef("utility", "Utility", (ClockTick(),)),
        )
