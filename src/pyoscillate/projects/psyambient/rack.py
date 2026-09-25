"""Patch definitions for the free-running psyambient rack."""

from pyoscillate.patches.base import FunctionVoice
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
        FunctionVoice.from_module(soundscape_fm, volume_default=0.6),
        name="soundscape_fm",
        title="Soundscape - chaotic FM pad",
        summary="Slow-morphing, unpredictable pad that never quite repeats itself.",
    ),
    PatchDef(
        FunctionVoice.from_module(soundscape_filter, volume_default=0.6),
        name="soundscape_filter",
        title="Soundscape - filter-swept pad",
        summary="Sustained drone whose brightness sweeps and breathes unpredictably.",
    ),
    PatchDef(
        FunctionVoice.from_module(soundscape_wash, volume_default=0.6),
        name="soundscape_wash",
        title="Soundscape - washy detuned pad",
        summary="Wide, hazy detuned wash that dissolves into echoing space.",
    ),
    PatchDef(
        FunctionVoice.from_module(
            mid_arp,
            volume_default=0.6,
            rebuild_parameters=("step_bars",),
            needs_tempo=True,
            needs_clock=True,
        ),
        name="mid_arp",
        title="Mid - slow pentatonic arpeggio",
        summary="Calm, consonant melodic line locked to the groove.",
    ),
    PatchDef(
        FunctionVoice.from_module(
            mid_generative,
            volume_default=0.6,
            rebuild_parameters=("note_period", "note_duration"),
        ),
        name="mid_generative",
        title="Mid - generative melody",
        summary="Ever-changing generative melody that never quite repeats.",
    ),
    PatchDef(
        FunctionVoice.from_module(
            mid_canon,
            volume_default=0.6,
            rebuild_parameters=(
                "voice_a_period",
                "voice_b_period",
                "voice_b_interval",
                "note_duration",
            ),
        ),
        name="mid_canon",
        title="Mid - two-voice canon",
        summary="Two melodic voices in a slow-shifting call and response.",
    ),
    PatchDef(
        FunctionVoice.from_module(bass_drone, volume_default=0.8),
        name="bass_drone",
        title="Bass - slow-swelling sub drone",
        summary="Slow-breathing sub bed that swells and recedes.",
    ),
    PatchDef(
        FunctionVoice.from_module(bass_chaos, volume_default=0.8),
        name="bass_chaos",
        title="Bass - chaotic sub drift",
        summary="Living, unstable sub rumble whose pitch subtly wanders.",
    ),
    PatchDef(
        FunctionVoice.from_module(bass_rumble, volume_default=0.8),
        name="bass_rumble",
        title="Bass - textural noise rumble",
        summary="Unpitched, earthquake-like low-end texture.",
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
