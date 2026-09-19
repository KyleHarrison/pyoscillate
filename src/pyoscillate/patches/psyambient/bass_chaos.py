from __future__ import annotations

from ipywidgets import HTML, Checkbox, FloatSlider, HBox, VBox, interactive_output
from pyo.lib.filters import MoogLP
from pyo.lib.generators import Rossler
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
    pitch_chaos = Rossler(pitch=chaos_speed, chaos=chaos_amount, mul=drift_range, add=root_freq)

    sub_table = HarmTable(SUB_HARMONICS)
    sub_osc = Osc(table=sub_table, freq=pitch_chaos, mul=0.5)
    voice = MoogLP(sub_osc, freq=filter_base, res=filter_res)

    return Patch(sequencer=ContinuousSequencer(), voice=voice)


def widget(rack: PatchRack, controller: PresetController | None = None) -> VBox:
    """Create bass_chaos controls with parameter descriptions beside each slider."""

    def set_params(
        enabled, root_freq, chaos_speed, chaos_amount, drift_range, filter_base, filter_res, volume
    ):
        if controller is not None and controller.applying:
            return
        if not enabled:
            rack.stop("bass_chaos")
            return

        patch = build(root_freq, chaos_speed, chaos_amount, drift_range, filter_base, filter_res)
        patch.volume = volume
        rack.start("bass_chaos", patch)

    enabled = Checkbox(value=False, description="bass_chaos on/off")
    root_freq = FloatSlider(min=20, max=80, step=1, value=ROOT_FREQ, description="root_freq")
    chaos_speed = FloatSlider(min=0.01, max=0.3, step=0.01, value=0.03, description="chaos_speed")
    chaos_amount = FloatSlider(min=0, max=1, step=0.05, value=0.5, description="chaos_amount")
    drift_range = FloatSlider(min=0, max=15, step=0.5, value=3.0, description="drift_range")
    filter_base = FloatSlider(min=60, max=500, step=10, value=180, description="filter_base")
    filter_res = FloatSlider(min=0, max=1, step=0.05, value=0.2, description="filter_res")
    volume = FloatSlider(min=0, max=2, step=0.1, value=0.8, description="volume")

    controls = {
        "enabled": enabled,
        "root_freq": root_freq,
        "chaos_speed": chaos_speed,
        "chaos_amount": chaos_amount,
        "drift_range": drift_range,
        "filter_base": filter_base,
        "filter_res": filter_res,
        "volume": volume,
    }
    if controller is not None:
        controller.register(
            "bass_chaos",
            controls,
            lambda: set_params(**{name: widget.value for name, widget in controls.items()}),
        )

    output = interactive_output(set_params, controls)
    slider_rows = [
        HBox([root_freq, HTML("Center frequency the pitch wanders around.")]),
        HBox([chaos_speed, HTML("How fast the pitch drifts - kept slow so it stays subliminal.")]),
        HBox([chaos_amount, HTML("How unpredictable the drift is - higher is less regular.")]),
        HBox(
            [
                drift_range,
                HTML("How far the pitch wanders - larger is more audible and unsettling."),
            ]
        ),
        HBox([filter_base, HTML("Lowpass cutoff - lower darkens and softens the rumble.")]),
        HBox([filter_res, HTML("Filter resonance - kept low for a smooth, uncolored low end.")]),
        HBox([volume, HTML("Output level for this patch, limited so it won't clip.")]),
    ]
    return VBox([enabled, *slider_rows, output])
