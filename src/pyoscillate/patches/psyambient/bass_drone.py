from __future__ import annotations

from ipywidgets import HTML, Checkbox, FloatSlider, HBox, VBox, interactive_output
from pyo.lib.filters import MoogLP
from pyo.lib.generators import Sine
from pyo.lib.tableprocess import Osc
from pyo.lib.tables import HarmTable

from pyoscillate.patches.base import Patch, PatchRack
from pyoscillate.patches.presets import PresetController
from pyoscillate.patches.psyambient.common import ContinuousSequencer

ROOT_FREQ = 41  # E1, current notebook default

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
    swell = Sine(freq=1 / swell_period, mul=swell_depth / 2, add=1 - swell_depth / 2)

    sub_table = HarmTable(SUB_HARMONICS)
    sub_osc = Osc(table=sub_table, freq=root_freq, mul=swell)
    voice = MoogLP(sub_osc, freq=filter_base, res=filter_res)

    return Patch(sequencer=ContinuousSequencer(), voice=voice)


def widget(rack: PatchRack, controller: PresetController | None = None) -> VBox:
    """Create bass_drone controls with parameter descriptions beside each slider."""

    def set_params(enabled, root_freq, swell_period, swell_depth, filter_base, filter_res, volume):
        if controller is not None and controller.applying:
            return
        if not enabled:
            rack.stop("bass_drone")
            return

        patch = build(root_freq, swell_period, swell_depth, filter_base, filter_res)
        patch.volume = volume
        rack.start("bass_drone", patch)

    enabled = Checkbox(value=False, description="bass_drone on/off")
    root_freq = FloatSlider(min=20, max=80, step=1, value=ROOT_FREQ, description="root_freq")
    swell_period = FloatSlider(min=2, max=30, step=0.5, value=9.0, description="swell_period")
    swell_depth = FloatSlider(min=0, max=1, step=0.05, value=0.4, description="swell_depth")
    filter_base = FloatSlider(min=60, max=500, step=10, value=180, description="filter_base")
    filter_res = FloatSlider(min=0, max=1, step=0.05, value=0.2, description="filter_res")
    volume = FloatSlider(min=0, max=2, step=0.1, value=0.8, description="volume")

    controls = {
        "enabled": enabled,
        "root_freq": root_freq,
        "swell_period": swell_period,
        "swell_depth": swell_depth,
        "filter_base": filter_base,
        "filter_res": filter_res,
        "volume": volume,
    }
    if controller is not None:
        controller.register(
            "bass_drone",
            controls,
            lambda: set_params(**{name: widget.value for name, widget in controls.items()}),
        )

    output = interactive_output(set_params, controls)
    slider_rows = [
        HBox([root_freq, HTML("Fundamental frequency of the sub tone.")]),
        HBox([swell_period, HTML("Seconds per swell cycle - longer feels like a slow tide.")]),
        HBox(
            [swell_depth, HTML("How dramatic the swell is - higher dips further toward silence.")]
        ),
        HBox([filter_base, HTML("Lowpass cutoff - lower darkens and softens the rumble.")]),
        HBox([filter_res, HTML("Filter resonance - kept low for a smooth, uncolored low end.")]),
        HBox([volume, HTML("Output level for this patch, limited so it won't clip.")]),
    ]
    return VBox([enabled, *slider_rows, output])
