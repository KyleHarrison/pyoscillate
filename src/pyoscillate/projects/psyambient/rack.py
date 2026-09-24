"""Patch definitions for the free-running psyambient rack."""

from pyoscillate.patches.musical.arp import arp as mid_arp
from pyoscillate.patches.musical.canon import canon as mid_canon
from pyoscillate.patches.musical.generative import generative as mid_generative
from pyoscillate.patches.texture.rumble import rumble as bass_rumble
from pyoscillate.patches.tonal.drone import filter as soundscape_filter
from pyoscillate.patches.tonal.drone import fm as soundscape_fm
from pyoscillate.patches.tonal.drone import sub_chaos as bass_chaos
from pyoscillate.patches.tonal.drone import sub_swell as bass_drone
from pyoscillate.patches.tonal.drone import wash as soundscape_wash
from src.flet.base import PatchDef, PatchGroupDef

# this project's own tempo - other projects set their own value instead of
# sharing one hardcoded in app.py
BPM = 70

PATCH_DEFS: list[PatchDef] = [
    PatchDef(
        "soundscape_fm",
        "Soundscape - chaotic FM pad",
        "Slow-morphing, unpredictable pad that never quite repeats itself.",
        soundscape_fm.build,
        soundscape_fm.PARAMETERS,
        0.6,
    ),
    PatchDef(
        "soundscape_filter",
        "Soundscape - filter-swept pad",
        "Sustained drone whose brightness sweeps and breathes unpredictably.",
        soundscape_filter.build,
        soundscape_filter.PARAMETERS,
        0.6,
    ),
    PatchDef(
        "soundscape_wash",
        "Soundscape - washy detuned pad",
        "Wide, hazy detuned wash that dissolves into echoing space.",
        soundscape_wash.build,
        soundscape_wash.PARAMETERS,
        0.6,
    ),
    PatchDef(
        "mid_arp",
        "Mid - slow pentatonic arpeggio",
        "Calm, consonant melodic line locked to the groove.",
        mid_arp.build,
        mid_arp.PARAMETERS,
        0.6,
        rebuild_parameters=("step_bars",),
        needs_tempo=True,
        needs_clock=True,
    ),
    PatchDef(
        "mid_generative",
        "Mid - generative melody",
        "Ever-changing generative melody that never quite repeats.",
        mid_generative.build,
        mid_generative.PARAMETERS,
        0.6,
        rebuild_parameters=("note_period", "note_duration"),
    ),
    PatchDef(
        "mid_canon",
        "Mid - two-voice canon",
        "Two melodic voices in a slow-shifting call and response.",
        mid_canon.build,
        mid_canon.PARAMETERS,
        0.6,
        rebuild_parameters=(
            "voice_a_period",
            "voice_b_period",
            "voice_b_interval",
            "note_duration",
        ),
    ),
    PatchDef(
        "bass_drone",
        "Bass - slow-swelling sub drone",
        "Slow-breathing sub bed that swells and recedes.",
        bass_drone.build,
        bass_drone.PARAMETERS,
        0.8,
    ),
    PatchDef(
        "bass_chaos",
        "Bass - chaotic sub drift",
        "Living, unstable sub rumble whose pitch subtly wanders.",
        bass_chaos.build,
        bass_chaos.PARAMETERS,
        0.8,
    ),
    PatchDef(
        "bass_rumble",
        "Bass - textural noise rumble",
        "Unpitched, earthquake-like low-end texture.",
        bass_rumble.build,
        bass_rumble.PARAMETERS,
        0.8,
    ),
]

PATCH_GROUPS: list[PatchGroupDef] = [
    PatchGroupDef(
        "soundscapes",
        "Soundscapes",
        tuple(PATCH_DEFS[0:3]),
        "Choose and combine evolving atmospheric beds.",
    ),
    PatchGroupDef(
        "mid",
        "Mid Voices",
        tuple(PATCH_DEFS[3:6]),
        "Melodic movement in the center of the arrangement.",
    ),
    PatchGroupDef(
        "bass",
        "Bass",
        tuple(PATCH_DEFS[6:9]),
        "Low-frequency foundations and textures.",
    ),
]
