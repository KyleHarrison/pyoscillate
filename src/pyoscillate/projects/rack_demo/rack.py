"""Patch definitions for the clock-locked groove demo."""

from pyoscillate.patches import atmosphere, bass, clock_tick, drone, hat, low_hat
from src.flet.base import PatchDef

PATCH_DEFS: list[PatchDef] = [
    PatchDef(
        "bass",
        "Bass",
        "Rolling 16-step bassline through a resonant, LFO-swept lowpass filter.",
        bass.build,
        bass.PARAMETERS,
        1.0,
        needs_tempo=True,
        needs_clock=True,
    ),
    PatchDef(
        "atmosphere",
        "Atmosphere (FM pad + arpeggiator)",
        "FM pad voice arpeggiated at 8th notes, with a slow amplitude swell and reverb.",
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
        "Subtle high-passed noise tick, once per 8th note.",
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
        "Darker noise tick, once per quarter note, as a rarer accent.",
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
        "Four free-running, resonant noise ticks.",
        clock_tick.build,
        clock_tick.PARAMETERS,
        1.0,
        needs_tempo=True,
    ),
    PatchDef(
        "drone",
        "Drone",
        "Slow-winding FM drone: note changes once every 8 bars.",
        drone.build,
        drone.PARAMETERS,
        1.0,
        needs_tempo=True,
        needs_clock=True,
    ),
]
