from __future__ import annotations

from ipywidgets import VBox
from pyo.lib.controls import SigTo
from pyo.lib.filters import MoogLP
from pyo.lib.generators import Sine
from pyo.lib.tableprocess import Osc
from pyo.lib.tables import HarmTable

from pyoscillate.patches.base import Patch, PatchRack
from pyoscillate.patches.common import ContinuousSequencer
from pyoscillate.patches.presets import PresetController
from pyoscillate.patches.widgets import PyoParamRef, SliderSpec, patch_widget

ROOT_FREQ = 41  # E1, current notebook default

PARAMETERS = (
    SliderSpec(
        "root_freq",
        20,
        80,
        1,
        ROOT_FREQ,
        "Register",
        "Sets the fixed pitch of the sub drone.",
        (PyoParamRef(Osc, "freq"),),
    ),
    SliderSpec(
        "swell_period",
        2,
        30,
        0.5,
        9.0,
        "Breathing rate",
        "How long one swell cycle takes; longer feels like a slow tide, shorter reads as a more rhythmic pulse.",
        (PyoParamRef(Sine, "freq"),),
    ),
    SliderSpec(
        "swell_depth",
        0,
        1,
        0.05,
        0.4,
        "Swell depth",
        "How dramatic the level swell is; higher makes the breathing more audible, lower keeps the drone closer to constant.",
        (PyoParamRef(Sine, "mul"),),
    ),
    SliderSpec(
        "filter_base",
        60,
        500,
        10,
        180,
        "Brightness",
        "Darkens or brightens the low end; lower keeps it duller and softer, higher lets more harmonic content through.",
        (PyoParamRef(MoogLP, "freq"),),
    ),
    SliderSpec(
        "filter_res",
        0,
        1,
        0.05,
        0.2,
        "Resonance",
        "Adds emphasis around the cutoff; kept low here so the drone stays smooth rather than whistly.",
        (PyoParamRef(MoogLP, "res"),),
    ),
)

# mostly fundamental with a touch of 2nd/3rd harmonic - rounded, sub-heavy tone
SUB_HARMONICS = [1, 0.15, 0.05]


def build(
    root_freq: float = ROOT_FREQ,
    swell_period: float = 9.0,
    swell_depth: float = 0.4,
    filter_base: float = 180,
    filter_res: float = 0.2,
) -> Patch:
    """Slow-swelling sub drone: a near-static low fundamental that breathes in and out in level rather than changing pitch or timbre.

    Args:
        root_freq: Fundamental frequency (Hz) of the sub tone. Kept low and
            fixed - this patch's movement comes entirely from the swell,
            not from pitch or timbral change.
        swell_period: Seconds for one full swell cycle (quiet-loud-quiet).
            Longer periods make the rumble feel like a slow tide; shorter
            periods make it read as a more rhythmic pulse.
        swell_depth: How far the level dips below its peak each swell
            cycle, 0-1. Higher values make the swell more dramatic and
            audible; lower values keep the rumble closer to constant.
        filter_base: Lowpass cutoff (Hz) applied after the oscillator,
            rounding off anything above the sub range. Lower values darken
            and soften the rumble further; higher values let more of the
            harmonic content through for a slightly more present tone.
        filter_res: `MoogLP` resonance (0-1ish). Kept low by default since
            a rumbling sub bed benefits from a smooth, uncolored low end
            rather than an emphasized, whistling resonant peak.
    """
    live = {
        name: SigTo(value=value, time=0.15)
        for name, value in {
            "root_freq": root_freq,
            "swell_period": swell_period,
            "swell_depth": swell_depth,
            "filter_base": filter_base,
            "filter_res": filter_res,
        }.items()
    }
    swell = Sine(
        freq=1 / live["swell_period"],
        mul=live["swell_depth"] / 2,
        add=1 - swell_depth / 2,
    )

    sub_table = HarmTable(SUB_HARMONICS)
    sub_osc = Osc(table=sub_table, freq=live["root_freq"], mul=swell)
    voice = MoogLP(sub_osc, freq=live["filter_base"], res=live["filter_res"])

    return Patch(
        sequencer=ContinuousSequencer(),
        voice=voice,
        controls={
            name: lambda value, control=control: setattr(control, "value", value)
            for name, control in live.items()
        },
    )


def widget(rack: PatchRack, controller: PresetController | None = None) -> VBox:
    """Create bass_drone controls."""
    return patch_widget(
        rack, "bass_drone", build, PARAMETERS, controller=controller, volume_default=0.8
    )
