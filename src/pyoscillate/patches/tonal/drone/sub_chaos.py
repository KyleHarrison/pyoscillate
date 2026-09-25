# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.drone.sub_chaos
from __future__ import annotations

from pyo.lib.controls import SigTo
from pyo.lib.filters import MoogLP
from pyo.lib.generators import Rossler
from pyo.lib.tableprocess import Osc
from pyo.lib.tables import HarmTable

from pyoscillate.patches.base import Patch
from pyoscillate.patches.common import ContinuousSequencer
from pyoscillate.patches.params import PyoParamRef, SliderSpec
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
        (PyoParamRef(Rossler, "add"),),
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
        (PyoParamRef(Rossler, "pitch"),),
    ),
    SliderSpec(
        "chaos_amount",
        0,
        1,
        0.05,
        0.5,
        "Instability",
        "How unpredictable the pitch wander is; higher feels more restless and alive, lower stays closer to a steady drone.",
        (PyoParamRef(Rossler, "chaos"),),
    ),
    SliderSpec(
        "drift_range",
        0,
        15,
        0.5,
        3.0,
        "Wander range",
        "How far the pitch strays from center; wider feels more organic and unsettled, narrower keeps it closer to a fixed note.",
        (PyoParamRef(Rossler, "mul"),),
    ),
    SliderSpec(
        "filter_base",
        60,
        500,
        10,
        180,
        "Brightness",
        "Darkens or brightens the low end; lower keeps it duller and rounder, higher lets a bit more presence through.",
        (PyoParamRef(MoogLP, "freq"),),
    ),
    SliderSpec(
        "filter_res",
        0,
        1,
        0.05,
        0.2,
        "Resonance",
        "Adds emphasis around the cutoff for a more colored, slightly whistling low end; kept low here for a smooth, uncolored rumble.",
        (PyoParamRef(MoogLP, "res"),),
    ),
)

# mostly fundamental with a touch of 2nd/3rd harmonic - rounded, sub-heavy tone
SUB_HARMONICS = [1, 0.15, 0.05]


def build(
    root_freq: float = ROOT_FREQ,
    chaos_speed: float = 0.03,
    chaos_amount: float = 0.5,
    drift_range: float = 3.0,
    filter_base: float = 180,
    filter_res: float = 0.2,
) -> Patch:
    """Chaotic sub drift: a near-static low fundamental whose pitch wanders unpredictably within a narrow range, for an organic, unstable rumble.

    Unlike `bass_drone`'s level-only swell, the movement here is in the
    pitch itself - kept narrow enough that it never reads as a clear note
    change, just a subtly living, breathing low end.

    Args:
        root_freq: Center frequency (Hz) the pitch wanders around.
        chaos_speed: `pitch` parameter of the `Rossler` attractor driving
            the frequency wander - how fast it drifts. Kept very slow by
            default so the movement stays subliminal rather than audible
            as pitch bending.
        chaos_amount: `chaos` parameter of the same attractor, 0-1. Higher
            values make the drift less predictable; lower values pull it
            toward smoother, more regular movement.
        drift_range: How far (Hz) the pitch wanders above and below
            `root_freq`. Larger values make the instability more audible
            and unsettling; smaller values keep it nearly imperceptible.
        filter_base: Lowpass cutoff (Hz) applied after the oscillator,
            rounding off anything above the sub range.
        filter_res: `MoogLP` resonance (0-1ish). Kept low by default for a
            smooth, uncolored low end.
    """
    live = {
        name: SigTo(value=value, time=0.15)
        for name, value in {
            "root_freq": root_freq,
            "chaos_speed": chaos_speed,
            "chaos_amount": chaos_amount,
            "drift_range": drift_range,
            "filter_base": filter_base,
            "filter_res": filter_res,
        }.items()
    }
    pitch_chaos = Rossler(
        pitch=live["chaos_speed"],
        chaos=live["chaos_amount"],
        mul=live["drift_range"],
        add=live["root_freq"],
    )

    sub_table = HarmTable(SUB_HARMONICS)
    sub_osc = Osc(table=sub_table, freq=pitch_chaos, mul=0.5)
    voice = MoogLP(sub_osc, freq=live["filter_base"], res=live["filter_res"])

    return Patch(
        sequencer=ContinuousSequencer(),
        voice=voice,
        controls={
            name: lambda value, control=control: setattr(control, "value", value)
            for name, control in live.items()
        },
        resources=(*live.values(), pitch_chaos, sub_table, sub_osc),
    )
