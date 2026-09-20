"""Flet port of `notebooks/psyambient/psyambient.ipynb`.

Nine free-running/generative ambient patches from `pyoscillate.patches.psyambient`,
composed onto one shared `PatchRack` via `src.flet.base.PatchRackApp`. Only
`mid_arp` needs the shared tempo/clock grid - everything else in this
notebook is deliberately free-running - but the clock is started regardless,
matching the notebook's Setup cell.
"""

from __future__ import annotations

from pathlib import Path

import flet as ft
from pyoscillate.patches.psyambient import (
    bass_chaos,
    bass_drone,
    bass_rumble,
    mid_arp,
    mid_canon,
    mid_generative,
    soundscape_filter,
    soundscape_fm,
    soundscape_wash,
)
from src.flet.base import EngineSpec, PatchDef, PatchRackApp

CATALOG_DIR = Path(__file__).parent / "presets" / "psyambient"

PATCH_DEFS = [
    PatchDef(
        name="soundscape_fm",
        title="Soundscape - chaotic FM pad",
        summary="Free-running FM pad driven by Rossler/Lorenz attractors.",
        build=soundscape_fm.build,
        parameters=soundscape_fm.PARAMETERS,
        volume_default=0.6,
    ),
    PatchDef(
        name="soundscape_filter",
        title="Soundscape - filter-swept pad",
        summary="Static drone carved by a chaotically-swept resonant lowpass filter.",
        build=soundscape_filter.build,
        parameters=soundscape_filter.PARAMETERS,
        volume_default=0.6,
    ),
    PatchDef(
        name="soundscape_wash",
        title="Soundscape - washy detuned pad",
        summary="SuperSaw smeared with chorus, reverb, and delay.",
        build=soundscape_wash.build,
        parameters=soundscape_wash.PARAMETERS,
        volume_default=0.6,
    ),
    PatchDef(
        name="mid_arp",
        title="Mid - slow pentatonic arpeggio",
        summary="Fixed pentatonic melody, phase-locked to the shared clock.",
        build=mid_arp.build,
        parameters=mid_arp.PARAMETERS,
        volume_default=0.6,
        rebuild_parameters=("step_bars",),
        needs_tempo=True,
        needs_clock=True,
    ),
    PatchDef(
        name="mid_generative",
        title="Mid - generative melody",
        summary="Free-running generative melody, drawn at random every few seconds.",
        build=mid_generative.build,
        parameters=mid_generative.PARAMETERS,
        volume_default=0.6,
        rebuild_parameters=("note_period", "note_duration"),
    ),
    PatchDef(
        name="mid_canon",
        title="Mid - two-voice canon",
        summary="Two generative melodic voices drifting in and out of alignment.",
        build=mid_canon.build,
        parameters=mid_canon.PARAMETERS,
        volume_default=0.6,
        rebuild_parameters=("voice_a_period", "voice_b_period", "voice_b_interval", "note_duration"),
    ),
    PatchDef(
        name="bass_drone",
        title="Bass - slow-swelling sub drone",
        summary="Near-static low fundamental that breathes in level.",
        build=bass_drone.build,
        parameters=bass_drone.PARAMETERS,
        volume_default=0.8,
    ),
    PatchDef(
        name="bass_chaos",
        title="Bass - chaotic sub drift",
        summary="Near-static low fundamental whose pitch wanders unpredictably.",
        build=bass_chaos.build,
        parameters=bass_chaos.PARAMETERS,
        volume_default=0.8,
    ),
    PatchDef(
        name="bass_rumble",
        title="Bass - textural noise rumble",
        summary="Filtered BrownNoise blended with a faint sub sine.",
        build=bass_rumble.build,
        parameters=bass_rumble.PARAMETERS,
        volume_default=0.8,
    ),
]


def main(page: ft.Page) -> None:
    PatchRackApp(
        page=page,
        title="Psyambient",
        subtitle="Ambient rack",
        catalog_dir=CATALOG_DIR,
        patch_defs=PATCH_DEFS,
        engine=EngineSpec(nchnls=2, bpm=70, needs_clock=True),
    )


if __name__ == "__main__":
    ft.run(main)
