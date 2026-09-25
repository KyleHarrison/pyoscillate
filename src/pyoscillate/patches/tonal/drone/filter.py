# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.drone.filter
from __future__ import annotations

from typing import Any

from pyo.lib.effects import Delay, Freeverb
from pyo.lib.filters import MoogLP
from pyo.lib.generators import Lorenz
from pyo.lib.tableprocess import Osc
from pyo.lib.tables import HarmTable

from pyoscillate.patches.base import Patch
from pyoscillate.patches.common import ContinuousVoice
from pyoscillate.patches.params import SliderSpec
from pyoscillate.patches.utility.notes import notes

ROOT_FREQ = notes.A3  # current default

PARAMETERS = (
    SliderSpec(
        "root_freq",
        notes.A1,
        notes.A4,
        1,
        ROOT_FREQ,
        "Register",
        "Sets the drone's fundamental pitch.",
        scale="note",
    ),
    SliderSpec(
        "cutoff_speed",
        0.01,
        0.5,
        0.01,
        0.05,
        "Sweep speed",
        "How quickly the filter's cutoff wanders; slower feels like a slow-breathing wah, faster feels more agitated.",
    ),
    SliderSpec(
        "cutoff_chaos",
        0,
        1,
        0.05,
        0.6,
        "Sweep instability",
        "How unpredictable the cutoff sweep is; higher feels more restless and alive, lower stays closer to a steady, cyclical wah.",
    ),
    SliderSpec(
        "filter_res",
        0,
        1,
        0.05,
        0.6,
        "Resonance",
        "Adds emphasis around the cutoff as it sweeps; higher makes the motion more vocal and whistling, lower keeps it smoother.",
    ),
    SliderSpec(
        "filter_base",
        100,
        2000,
        10,
        700,
        "Brightness",
        "Sets the average brightness the filter sweeps around; higher opens the drone up, lower keeps it duller and more closed.",
    ),
    SliderSpec(
        "filter_range",
        0,
        1500,
        10,
        600,
        "Sweep depth",
        "Controls how far the filter sweeps each cycle; wider ranges create more dramatic movement, narrower keeps the tone closer to static.",
    ),
    SliderSpec(
        "reverb_size",
        0,
        1,
        0.05,
        0.8,
        "Space",
        "Sets how large and distant the drone's room feels, from a tight presence to a huge, cavernous decay.",
    ),
    SliderSpec(
        "reverb_damp",
        0,
        1,
        0.05,
        0.5,
        "Tail darkness",
        "Darkens the reverb tail as it decays; higher settings sound warmer and more muffled, lower settings stay bright and shimmering.",
    ),
    SliderSpec(
        "reverb_bal",
        0,
        1,
        0.05,
        0.75,
        "Distance",
        "Blends how much of the drone is heard through the reverb versus dry; higher dissolves it into the atmosphere, lower keeps it present.",
    ),
    SliderSpec(
        "delay_time",
        0.05,
        2,
        0.05,
        0.45,
        "Echo spacing",
        "Sets the time between echo repeats, smearing the timbral drift across time.",
    ),
    SliderSpec(
        "delay_feedback",
        0,
        0.9,
        0.05,
        0.3,
        "Echo density",
        "Sets how many times each echo repeats before fading; higher creates a denser, more layered wash.",
    ),
)

# harmonic-rich static tone for the filter to carve movement into - the pad's
# "color" comes entirely from the cutoff sweep below, not from this waveform changing
PAD_HARMONICS = [1, 0.6, 0.4, 0.25, 0.15, 0.08, 0.04]
VOLUME_DEFAULT = 0.6


class SoundscapeFilter(ContinuousVoice):
    """Static harmonic-rich drone carved by a chaotically-swept resonant lowpass filter.

    Unlike `SoundscapeFm`'s smooth FM timbre drift, all the movement here
    comes from the filter cutoff wandering - a more angular, "breathing"
    character closer to a classic 60s/70s psychedelic filter sweep than a
    softly evolving tone.
    """

    title = "Soundscape - filter-swept pad"
    summary = "Sustained drone whose brightness sweeps and breathes unpredictably."
    parameters = PARAMETERS
    volume_default = VOLUME_DEFAULT

    root_freq: float
    cutoff_speed: float
    cutoff_chaos: float
    filter_res: float
    filter_base: float
    filter_range: float
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
            "cutoff_speed",
            "cutoff_chaos",
            "filter_res",
            "filter_base",
            "filter_range",
            "reverb_size",
            "reverb_damp",
            "reverb_bal",
            "delay_time",
            "delay_feedback",
        )
        pad_table = HarmTable(PAD_HARMONICS)
        pad_osc = Osc(table=pad_table, freq=live["root_freq"], mul=0.25)

        cutoff_chaos_lfo = Lorenz(
            pitch=live["cutoff_speed"],
            chaos=live["cutoff_chaos"],
            mul=live["filter_range"],
            add=live["filter_base"],
        )
        filtered = MoogLP(pad_osc, freq=cutoff_chaos_lfo, res=live["filter_res"])

        reverb_voice = Freeverb(
            filtered,
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
        self.retain(pad_table, pad_osc, cutoff_chaos_lfo, filtered, reverb_voice)
        return self.finish(voice)
