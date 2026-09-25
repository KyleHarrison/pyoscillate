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
        "soundscape_fm",
        "Soundscape - chaotic FM pad",
        "Slow-morphing, unpredictable pad that never quite repeats itself.",
        FunctionVoice.from_module(soundscape_fm, volume_default=0.6),
    ),
    PatchDef(
        "soundscape_filter",
        "Soundscape - filter-swept pad",
        "Sustained drone whose brightness sweeps and breathes unpredictably.",
        FunctionVoice.from_module(soundscape_filter, volume_default=0.6),
    ),
    PatchDef(
        "soundscape_wash",
        "Soundscape - washy detuned pad",
        "Wide, hazy detuned wash that dissolves into echoing space.",
        FunctionVoice.from_module(soundscape_wash, volume_default=0.6),
    ),
    PatchDef(
        "mid_arp",
        "Mid - slow pentatonic arpeggio",
        "Calm, consonant melodic line locked to the groove.",
        FunctionVoice.from_module(
            mid_arp,
            volume_default=0.6,
            rebuild_parameters=("step_bars",),
            needs_tempo=True,
            needs_clock=True,
        ),
    ),
    PatchDef(
        "mid_generative",
        "Mid - generative melody",
        "Ever-changing generative melody that never quite repeats.",
        FunctionVoice.from_module(
            mid_generative,
            volume_default=0.6,
            rebuild_parameters=("note_period", "note_duration"),
        ),
    ),
    PatchDef(
        "mid_canon",
        "Mid - two-voice canon",
        "Two melodic voices in a slow-shifting call and response.",
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
    ),
    PatchDef(
        "bass_drone",
        "Bass - slow-swelling sub drone",
        "Slow-breathing sub bed that swells and recedes.",
        FunctionVoice.from_module(bass_drone, volume_default=0.8),
    ),
    PatchDef(
        "bass_chaos",
        "Bass - chaotic sub drift",
        "Living, unstable sub rumble whose pitch subtly wanders.",
        FunctionVoice.from_module(bass_chaos, volume_default=0.8),
    ),
    PatchDef(
        "bass_rumble",
        "Bass - textural noise rumble",
        "Unpitched, earthquake-like low-end texture.",
        FunctionVoice.from_module(bass_rumble, volume_default=0.8),
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
