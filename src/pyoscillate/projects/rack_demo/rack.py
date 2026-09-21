"""Patch definitions for the clock-locked groove demo."""

from pyoscillate.patches.drums import hat, low_hat
from pyoscillate.patches.musical import clock_tick
from pyoscillate.patches.texture import atmosphere
from pyoscillate.patches.tonal import bass, drone
from src.flet.base import PatchDef, PatchGroupDef

# this project's own tempo - other projects set their own value instead of
# sharing one hardcoded in app.py
BPM = 132

PATCH_DEFS: list[PatchDef] = [
    PatchDef(
        "bass",
        "Bass",
        "Rolling, resonant bassline that sweeps in tone across the groove.",
        bass.build,
        bass.PARAMETERS,
        1.0,
        needs_tempo=True,
        needs_clock=True,
    ),
    PatchDef(
        "atmosphere",
        "Atmosphere (FM pad + arpeggiator)",
        "Breathing melodic pad that arpeggiates and swells overhead.",
        atmosphere.build,
        atmosphere.PARAMETERS,
        0.6,
        rebuild_parameters=("step_division",),
        needs_tempo=True,
        needs_clock=True,
    ),
    PatchDef(
        "hat",
        "Hi-hat",
        "Subtle, airy top-end pulse.",
        hat.build,
        hat.PARAMETERS,
        0.2,
        rebuild_parameters=("decay",),
        needs_tempo=True,
        needs_clock=True,
    ),
    PatchDef(
        "low_hat",
        "Low hat",
        "Darker, rarer accent beneath the main hat.",
        low_hat.build,
        low_hat.PARAMETERS,
        0.2,
        rebuild_parameters=("decay",),
        needs_tempo=True,
        needs_clock=True,
    ),
    PatchDef(
        "clock_tick",
        "Clock tick",
        "Drifting clockwork texture of overlapping ticks.",
        clock_tick.build,
        clock_tick.PARAMETERS,
        1.0,
        needs_tempo=True,
    ),
    PatchDef(
        "drone",
        "Drone",
        "Slow-winding sustained drone that rarely changes note.",
        drone.build,
        drone.PARAMETERS,
        1.0,
        needs_tempo=True,
        needs_clock=True,
    ),
]

PATCH_GROUPS: list[PatchGroupDef] = [
    PatchGroupDef("rhythm", "Rhythm", (PATCH_DEFS[0], PATCH_DEFS[2], PATCH_DEFS[3])),
    PatchGroupDef("atmosphere", "Atmosphere", (PATCH_DEFS[1], PATCH_DEFS[5])),
    PatchGroupDef("utility", "Utility", (PATCH_DEFS[4],)),
]
