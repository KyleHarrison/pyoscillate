"""Patch definitions for the clock-locked groove demo."""

from pyoscillate.patches import atmosphere, bass, clock_tick, drone, hat, low_hat
from src.flet.base import PatchDef

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
