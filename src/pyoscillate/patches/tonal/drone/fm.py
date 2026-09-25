# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.drone.fm
from __future__ import annotations

from typing import Any

from pyo.lib.effects import Delay, Freeverb
from pyo.lib.generators import FM, Lorenz, Rossler

from pyoscillate.patches.base import Patch
from pyoscillate.patches.common import ContinuousVoice
from pyoscillate.patches.params import PyoParamRef, SliderSpec
from pyoscillate.patches.utility.notes import notes

ROOT_FREQ = notes.A2  # current default

PARAMETERS = (
    SliderSpec(
        "root_freq",
        notes.A1,
        notes.A3,
        1,
        ROOT_FREQ,
        "Register",
        "Sets the pad's held pitch, the carrier tone everything else is built on.",
        (PyoParamRef(FM, "carrier"),),
        scale="note",
    ),
    SliderSpec(
        "chaos_speed",
        0.01,
        0.5,
        0.01,
        0.04,
        "Drift speed",
        "How fast the pad's timbre wanders; lower is slower and more hypnotic, higher feels more restless.",
        (PyoParamRef(Rossler, "pitch"), PyoParamRef(Lorenz, "pitch")),
    ),
    SliderSpec(
        "chaos_amount",
        0,
        1,
        0.05,
        0.6,
        "Instability",
        "How unpredictable the wander is; higher feels more psychedelic and alive, lower stays closer to a steady tone.",
        (PyoParamRef(Rossler, "chaos"), PyoParamRef(Lorenz, "chaos")),
    ),
    SliderSpec(
        "reverb_size",
        0,
        1,
        0.05,
        0.85,
        "Space",
        "Sets how enveloping the pad's room feels; larger is more immersive and distant.",
        (PyoParamRef(Freeverb, "size"),),
    ),
    SliderSpec(
        "reverb_damp",
        0,
        1,
        0.05,
        0.4,
        "Tail darkness",
        "Darkens the reverb tail as it decays; higher is warmer and more muffled, lower stays brighter and shimmering.",
        (PyoParamRef(Freeverb, "damp"),),
    ),
    SliderSpec(
        "reverb_bal",
        0,
        1,
        0.05,
        0.85,
        "Distance",
        "Blends how much of the pad is heard through the reverb versus dry; higher dissolves it into the space, lower keeps it present.",
        (PyoParamRef(Freeverb, "bal"),),
    ),
    SliderSpec(
        "delay_time",
        0.05,
        2,
        0.05,
        0.6,
        "Echo spacing",
        "Sets the time between echo repeats, smearing the timbral drift across time.",
        (PyoParamRef(Delay, "delay"),),
    ),
    SliderSpec(
        "delay_feedback",
        0,
        0.9,
        0.05,
        0.35,
        "Echo density",
        "Sets how many times each echo repeats before decaying; higher creates a denser, more layered wash.",
        (PyoParamRef(Delay, "feedback"),),
    ),
)
VOLUME_DEFAULT = 0.6


class SoundscapeFm(ContinuousVoice):
    """Free-running FM pad whose timbre is driven entirely by chaotic attractors, with no clocked note pattern at all.

    Rossler wanders smoothly, Lorenz more angularly - pairing them on ratio
    and index gives the timbre two independently-textured axes of drift
    instead of both parameters moving in the same "shape" of way.
    """

    title = "Soundscape - chaotic FM pad"
    summary = "Slow-morphing, unpredictable pad that never quite repeats itself."
    parameters = PARAMETERS
    volume_default = VOLUME_DEFAULT

    root_freq: float
    chaos_speed: float
    chaos_amount: float
    reverb_size: float
    reverb_damp: float
    reverb_bal: float
    delay_time: float
    delay_feedback: float

    def build(self, **values: Any) -> Patch:
        self.configure(**values)
        self._reset()
        live = self.live_all(
            "root_freq",
            "chaos_speed",
            "chaos_amount",
            "reverb_size",
            "reverb_damp",
            "reverb_bal",
            "delay_time",
            "delay_feedback",
        )

        ratio_chaos = Rossler(pitch=live["chaos_speed"], chaos=live["chaos_amount"], mul=0.4, add=1.5)
        index_speed = live["chaos_speed"] * 1.3
        index_chaos = Lorenz(pitch=index_speed, chaos=live["chaos_amount"], mul=3, add=4)

        fm_voice = FM(carrier=live["root_freq"], ratio=ratio_chaos, index=index_chaos, mul=0.2)
        reverb_voice = Freeverb(
            fm_voice,
            size=live["reverb_size"],
            damp=live["reverb_damp"],
            bal=live["reverb_bal"],
        )
        voice = Delay(
            reverb_voice,
            delay=live["delay_time"],
            feedback=live["delay_feedback"],
            maxdelay=2,
        )
        self.retain(ratio_chaos, index_speed, index_chaos, fm_voice, reverb_voice)
        return self.finish(voice)
