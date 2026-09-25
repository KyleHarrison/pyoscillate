# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.drone.sub_chaos
from __future__ import annotations

from typing import Any

from pyo.lib.filters import MoogLP
from pyo.lib.generators import Rossler
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
        "Sets the center pitch the sub wanders around.",
        scale="note",
    ),
    SliderSpec(
        "chaos_speed",
        0.01,
        0.3,
        0.01,
        0.03,
        "Drift speed",
        "How quickly the pitch wanders; slower feels like a slow-breathing organism, faster feels more agitated and unstable.",
    ),
    SliderSpec(
        "chaos_amount",
        0,
        1,
        0.05,
        0.5,
        "Instability",
        "How unpredictable the pitch wander is; higher feels more restless and alive, lower stays closer to a steady drone.",
    ),
    SliderSpec(
        "drift_range",
        0,
        15,
        0.5,
        3.0,
        "Wander range",
        "How far the pitch strays from center; wider feels more organic and unsettled, narrower keeps it closer to a fixed note.",
    ),
    SliderSpec(
        "filter_base",
        60,
        500,
        10,
        180,
        "Brightness",
        "Darkens or brightens the low end; lower keeps it duller and rounder, higher lets a bit more presence through.",
    ),
    SliderSpec(
        "filter_res",
        0,
        1,
        0.05,
        0.2,
        "Resonance",
        "Adds emphasis around the cutoff for a more colored, slightly whistling low end; kept low here for a smooth, uncolored rumble.",
    ),
)

# mostly fundamental with a touch of 2nd/3rd harmonic - rounded, sub-heavy tone
SUB_HARMONICS = [1, 0.15, 0.05]
VOLUME_DEFAULT = 0.8


class BassChaos(ContinuousVoice):
    """Chaotic sub drift: a near-static low fundamental whose pitch wanders unpredictably within a narrow range, for an organic, unstable rumble.

    Unlike `BassDrone`'s level-only swell, the movement here is in the
    pitch itself - kept narrow enough that it never reads as a clear note
    change, just a subtly living, breathing low end.
    """

    title = "Bass - chaotic sub drift"
    summary = "Living, unstable sub rumble whose pitch subtly wanders."
    parameters = PARAMETERS
    volume_default = VOLUME_DEFAULT

    root_freq: float
    chaos_speed: float
    chaos_amount: float
    drift_range: float
    filter_base: float
    filter_res: float

    def build(self, **values: Any) -> Patch:
        self.configure(**values)
        self._reset()
        live = self.live_all(
            "root_freq", "chaos_speed", "chaos_amount", "drift_range", "filter_base", "filter_res"
        )
        pitch_chaos = Rossler(
            pitch=live["chaos_speed"],
            chaos=live["chaos_amount"],
            mul=live["drift_range"],
            add=live["root_freq"],
        )

        sub_table = HarmTable(SUB_HARMONICS)
        sub_osc = Osc(table=sub_table, freq=pitch_chaos, mul=0.5)
        voice = MoogLP(sub_osc, freq=live["filter_base"], res=live["filter_res"])
        self.retain(pitch_chaos, sub_table, sub_osc)
        return self.finish(voice)
