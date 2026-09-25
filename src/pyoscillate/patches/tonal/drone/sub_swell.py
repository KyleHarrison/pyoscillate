# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.drone.sub_swell
from __future__ import annotations

from typing import Any

from pyo.lib.filters import MoogLP
from pyo.lib.generators import Sine
from pyo.lib.tableprocess import Osc
from pyo.lib.tables import HarmTable

from pyoscillate.patches.base import Patch
from pyoscillate.patches.common import ContinuousVoice
from pyoscillate.patches.params import SliderSpec
from pyoscillate.patches.utility.notes import notes

ROOT_FREQ = notes.E1  # current default

PARAMETERS = (
    SliderSpec(
        "root_freq",
        notes.E0,
        notes.E2,
        1,
        ROOT_FREQ,
        "Register",
        "Sets the fixed pitch of the sub drone.",
        scale="note",
    ),
    SliderSpec(
        "swell_period",
        2,
        30,
        0.5,
        9.0,
        "Breathing rate",
        "How long one swell cycle takes; longer feels like a slow tide, shorter reads as a more rhythmic pulse.",
    ),
    SliderSpec(
        "swell_depth",
        0,
        1,
        0.05,
        0.4,
        "Swell depth",
        "How dramatic the level swell is; higher makes the breathing more audible, lower keeps the drone closer to constant.",
    ),
    SliderSpec(
        "filter_base",
        60,
        500,
        10,
        180,
        "Brightness",
        "Darkens or brightens the low end; lower keeps it duller and softer, higher lets more harmonic content through.",
    ),
    SliderSpec(
        "filter_res",
        0,
        1,
        0.05,
        0.2,
        "Resonance",
        "Adds emphasis around the cutoff; kept low here so the drone stays smooth rather than whistly.",
    ),
)

# mostly fundamental with a touch of 2nd/3rd harmonic - rounded, sub-heavy tone
SUB_HARMONICS = [1, 0.15, 0.05]
VOLUME_DEFAULT = 0.8


class BassDrone(ContinuousVoice):
    """Slow-swelling sub drone: a near-static low fundamental that breathes in and out in level rather than changing pitch or timbre."""

    title = "Bass - slow-swelling sub drone"
    summary = "Slow-breathing sub bed that swells and recedes."
    parameters = PARAMETERS
    volume_default = VOLUME_DEFAULT

    root_freq: float
    swell_period: float
    swell_depth: float
    filter_base: float
    filter_res: float

    def build(self, **values: Any) -> Patch:
        self.configure(**values)
        self._reset()
        live = self.live_all(
            "root_freq", "swell_period", "swell_depth", "filter_base", "filter_res"
        )

        swell_frequency = 1 / live["swell_period"]
        swell_amplitude = live["swell_depth"] / 2
        swell = Sine(
            freq=swell_frequency,
            mul=swell_amplitude,
            add=1 - self.swell_depth / 2,
        )

        sub_table = HarmTable(SUB_HARMONICS)
        sub_osc = Osc(table=sub_table, freq=live["root_freq"], mul=swell)
        voice = MoogLP(sub_osc, freq=live["filter_base"], res=live["filter_res"])
        self.retain(swell_frequency, swell_amplitude, swell, sub_table, sub_osc)
        return self.finish(voice)
