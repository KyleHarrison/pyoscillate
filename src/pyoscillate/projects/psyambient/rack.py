# Run: uv run flet run src/flet/psyambient/app.py
"""Patch definitions for the free-running psyambient rack."""

from pyoscillate.controller import (
    GroupControl,
    GroupController,
    ParamControl,
    Slot,
    SlotTarget,
)
from pyoscillate.patches.evolve import Evolve
from pyoscillate.patches.musical.arp.arp import Arp
from pyoscillate.patches.musical.canon.canon import Canon
from pyoscillate.patches.musical.generative.generative import Generative
from pyoscillate.patches.params import SliderSpec
from pyoscillate.patches.texture.rumble.rumble import BassRumble
from pyoscillate.patches.tonal.drone.filter import SoundscapeFilter
from pyoscillate.patches.tonal.drone.fm import SoundscapeFm
from pyoscillate.patches.tonal.drone.sub_chaos import BassChaos
from pyoscillate.patches.tonal.drone.sub_swell import BassDrone
from pyoscillate.patches.tonal.drone.wash import SoundscapeWash
from pyoscillate.projects.base import Rack


class PsyambientRack(Rack):
    """The free-running psyambient rack: evolving pads, slow generative mid
    voices and a sub bed. Each layer has a slider for how much it moves, and
    the Atmosphere slider moves all three together."""

    # this project's own tempo - other projects set their own value instead of
    # sharing one hardcoded in app.py
    bpm = 70

    soundscape_fm = Slot(SoundscapeFm)
    soundscape_filter = Slot(SoundscapeFilter)
    soundscape_wash = Slot(SoundscapeWash, evolve=Evolve(16))
    mid_arp = Slot(Arp)
    mid_generative = Slot(Generative)
    mid_canon = Slot(Canon)
    bass_drone = Slot(BassDrone)
    bass_chaos = Slot(BassChaos)
    bass_rumble = Slot(BassRumble)

    soundscape_drift = GroupControl(
        SliderSpec(
            "drift",
            0,
            1,
            0.05,
            0,
            "Drift",
            "Speeds up and widens the pads' wandering, from glacial to restless.",
        ),
        (
            SlotTarget(
                soundscape_fm,
                (
                    ParamControl(SoundscapeFm.chaos_speed, 0.04, 0.2),
                    ParamControl(SoundscapeFm.chaos_amount, 0.6, 1.0),
                ),
            ),
            SlotTarget(
                soundscape_filter,
                (
                    ParamControl(SoundscapeFilter.cutoff_speed, 0.05, 0.25),
                    ParamControl(SoundscapeFilter.cutoff_chaos, 0.6, 1.0),
                ),
            ),
            SlotTarget(
                soundscape_wash,
                (ParamControl(SoundscapeWash.pitch_drift, 0.03, 0.3),),
            ),
        ),
    )
    # the wash rotates its chorus depth and echo feedback every 16 bars
    soundscapes_group = GroupController(
        "Soundscapes",
        (soundscape_fm, soundscape_filter, soundscape_wash),
        "Choose and combine evolving atmospheric beds.",
        controls=(soundscape_drift,),
    )

    mid_shimmer = GroupControl(
        SliderSpec(
            "shimmer",
            0,
            1,
            0.05,
            0,
            "Shimmer",
            "Raises the FM index for a brighter, glassier tone.",
        ),
        (
            SlotTarget(mid_arp, (ParamControl(Arp.fm_index, 1.5, 4.0),)),
            SlotTarget(mid_generative, (ParamControl(Generative.fm_index, 1.5, 4.0),)),
            SlotTarget(mid_canon, (ParamControl(Canon.fm_index, 1.5, 4.0),)),
        ),
    )
    mid_group = GroupController(
        "Mid Voices",
        (mid_arp, mid_generative, mid_canon),
        "Phrased movement in the center of the arrangement.",
        controls=(mid_shimmer,),
    )

    bass_depth = GroupControl(
        SliderSpec(
            "depth",
            0,
            1,
            0.05,
            0,
            "Depth",
            "Opens the sub filters and deepens the swell and rumble.",
        ),
        (
            SlotTarget(
                bass_drone,
                (
                    ParamControl(BassDrone.filter_base, 180, 400),
                    ParamControl(BassDrone.swell_depth, 0.4, 0.9),
                ),
            ),
            SlotTarget(bass_chaos, (ParamControl(BassChaos.filter_base, 180, 400),)),
            SlotTarget(bass_rumble, (ParamControl(BassRumble.noise_level, 0.5, 0.9),)),
        ),
    )
    bass_group = GroupController(
        "Bass",
        (bass_drone, bass_chaos, bass_rumble),
        "Low-frequency foundations and textures.",
        controls=(bass_depth,),
    )

    atmosphere_intensity = GroupControl(
        SliderSpec(
            "intensity",
            0,
            1,
            0.05,
            0,
            "Intensity",
            "Makes the pads drift faster, the mid voices glassier and the bass deeper.",
        ),
        (soundscape_drift, mid_shimmer, bass_depth),
    )
    atmosphere_group = GroupController(
        "Atmosphere",
        (soundscapes_group, mid_group, bass_group),
        "Pads, mid voices and bass together.",
        controls=(atmosphere_intensity,),
    )
