from __future__ import annotations

from ipywidgets import VBox
from pyo.lib.controls import SigTo
from pyo.lib.effects import Delay, Freeverb
from pyo.lib.filters import MoogLP
from pyo.lib.generators import Lorenz
from pyo.lib.tableprocess import Osc
from pyo.lib.tables import HarmTable

from pyoscillate.patches.base import Patch, PatchRack
from pyoscillate.patches.presets import PresetController
from pyoscillate.patches.psyambient.common import ContinuousSequencer
from pyoscillate.patches.widgets import PyoParamRef, SliderSpec, patch_widget

ROOT_FREQ = 220  # A3, current default

PARAMETERS = (
    SliderSpec(
        "root_freq",
        55,
        440,
        1,
        ROOT_FREQ,
        "Root frequency",
        "Fundamental frequency.",
        (PyoParamRef(Osc, "freq"),),
    ),
    SliderSpec(
        "cutoff_speed",
        0.01,
        0.5,
        0.01,
        0.05,
        "Cutoff speed",
        "How fast the cutoff wanders.",
        (PyoParamRef(Lorenz, "pitch"),),
    ),
    SliderSpec(
        "cutoff_chaos",
        0,
        1,
        0.05,
        0.6,
        "Cutoff chaos",
        "How unpredictable the sweep is.",
        (PyoParamRef(Lorenz, "chaos"),),
    ),
    SliderSpec(
        "filter_res",
        0,
        1,
        0.05,
        0.6,
        "Filter resonance",
        "Lowpass resonance.",
        (PyoParamRef(MoogLP, "res"),),
    ),
    SliderSpec(
        "filter_base",
        100,
        2000,
        10,
        700,
        "Filter base",
        "Center cutoff frequency.",
        (PyoParamRef(Lorenz, "add"),),
    ),
    SliderSpec(
        "filter_range",
        0,
        1500,
        10,
        600,
        "Filter range",
        "Cutoff movement range.",
        (PyoParamRef(Lorenz, "mul"),),
    ),
    SliderSpec(
        "reverb_size",
        0,
        1,
        0.05,
        0.8,
        "Reverb size",
        "Reverb room size.",
        (PyoParamRef(Freeverb, "size"),),
    ),
    SliderSpec(
        "reverb_damp",
        0,
        1,
        0.05,
        0.5,
        "Reverb damping",
        "Reverb damping.",
        (PyoParamRef(Freeverb, "damp"),),
    ),
    SliderSpec(
        "reverb_bal",
        0,
        1,
        0.05,
        0.75,
        "Reverb balance",
        "Reverb dry/wet balance.",
        (PyoParamRef(Freeverb, "bal"),),
    ),
    SliderSpec(
        "delay_time",
        0.05,
        2,
        0.05,
        0.45,
        "Delay time",
        "Delay line time.",
        (PyoParamRef(Delay, "delay"),),
    ),
    SliderSpec(
        "delay_feedback",
        0,
        0.9,
        0.05,
        0.3,
        "Delay feedback",
        "Delay feedback.",
        (PyoParamRef(Delay, "feedback"),),
    ),
)

# harmonic-rich static tone for the filter to carve movement into - the pad's
# "color" comes entirely from the cutoff sweep below, not from this waveform changing
PAD_HARMONICS = [1, 0.6, 0.4, 0.25, 0.15, 0.08, 0.04]


def build(
    root_freq: float = ROOT_FREQ,
    cutoff_speed: float = 0.05,
    cutoff_chaos: float = 0.6,
    filter_res: float = 0.6,
    filter_base: float = 700,
    filter_range: float = 600,
    reverb_size: float = 0.8,
    reverb_damp: float = 0.5,
    reverb_bal: float = 0.75,
    delay_time: float = 0.45,
    delay_feedback: float = 0.3,
) -> Patch:
    """Static harmonic-rich drone carved by a chaotically-swept resonant lowpass filter.

    Unlike `soundscape_fm`'s smooth FM timbre drift, all the movement here
    comes from the filter cutoff wandering - a more angular, "breathing"
    character closer to a classic 60s/70s psychedelic filter sweep than a
    softly evolving tone.

    Args:
        root_freq: Fundamental frequency (Hz) of the static harmonic tone
            under the filter. The pitch never changes; only the filter
            cutoff moves.
        cutoff_speed: `pitch` parameter of the `Lorenz` attractor driving the
            filter cutoff - how fast it wanders. Lower values give a slow,
            spacious sweep; raising it makes the filter audibly restless.
        cutoff_chaos: `chaos` parameter of the same attractor, 0-1. Higher
            values make the sweep more unpredictable and angular; lower
            values pull it toward smoother, more periodic movement.
        filter_res: `MoogLP` resonance (0-1ish, self-oscillates as it
            approaches/exceeds 1). Higher values emphasize whatever
            frequency the sweep is currently sitting on, giving the pad a
            more pronounced, vocal-like "wah" as the cutoff wanders; lower
            values give a smoother, less colored response.
        filter_base: Center cutoff frequency (Hz) the wander rides on top
            of. Raising it lets more harmonics through on average, for a
            brighter pad; lowering it darkens and rounds it off.
        filter_range: How far (Hz) the attractor swings the cutoff above and
            below `filter_base`. Larger values make the sweep more dramatic
            - the pad audibly opens and closes; smaller values keep the
            cutoff nearly static for a more constant tone.
        reverb_size: Freeverb room size (0-1). Large by default so the pad
            reads as an enveloping space rather than a distinct voice.
        reverb_damp: Freeverb high-frequency damping (0-1). Higher values
            darken the tail; lower values keep it bright and ringing.
        reverb_bal: Freeverb dry/wet balance (0-1). Kept high so the pad is
            heard mostly through its reverb space.
        delay_time: Delay line time in seconds, thickening the sweep's
            drift by echoing each moment of it slightly later.
        delay_feedback: Delay feedback (0-1). Higher values repeat each
            echo more times before decaying, for a denser wash.
    """
    live = {
        name: SigTo(value=value, time=0.15)
        for name, value in {
            "root_freq": root_freq,
            "cutoff_speed": cutoff_speed,
            "cutoff_chaos": cutoff_chaos,
            "filter_res": filter_res,
            "filter_base": filter_base,
            "filter_range": filter_range,
            "reverb_size": reverb_size,
            "reverb_damp": reverb_damp,
            "reverb_bal": reverb_bal,
            "delay_time": delay_time,
            "delay_feedback": delay_feedback,
        }.items()
    }
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

    return Patch(
        sequencer=ContinuousSequencer(),
        voice=voice,
        controls={
            name: lambda value, control=control: setattr(control, "value", value)
            for name, control in live.items()
        },
    )


def widget(rack: PatchRack, controller: PresetController | None = None) -> VBox:
    """Create soundscape_filter controls."""
    return patch_widget(rack, "soundscape_filter", build, PARAMETERS, controller=controller)

    """

    def set_params(
        enabled,
        root_freq,
        cutoff_speed,
        cutoff_chaos,
        filter_res,
        filter_base,
        filter_range,
        reverb_size,
        reverb_damp,
        reverb_bal,
        delay_time,
        delay_feedback,
        volume,
    ):
        if controller is not None and controller.applying:
            return
        if not enabled:
            rack.stop("soundscape_filter")
            return

        patch = build(
            root_freq,
            cutoff_speed,
            cutoff_chaos,
            filter_res,
            filter_base,
            filter_range,
            reverb_size,
            reverb_damp,
            reverb_bal,
            delay_time,
            delay_feedback,
        )
        patch.volume = volume
        rack.start("soundscape_filter", patch)

    enabled = Checkbox(value=False, description="soundscape_filter on/off")
    root_freq = FloatSlider(
        min=55,
        max=440,
        step=1,
        value=ROOT_FREQ,
        description="root_freq",
    )
    cutoff_speed = FloatSlider(
        min=0.01,
        max=0.5,
        step=0.01,
        value=0.05,
        description="cutoff_speed",
    )
    cutoff_chaos = FloatSlider(
        min=0,
        max=1,
        step=0.05,
        value=0.6,
        description="cutoff_chaos",
    )
    filter_res = FloatSlider(
        min=0,
        max=1,
        step=0.05,
        value=0.6,
        description="filter_res",
    )
    filter_base = FloatSlider(
        min=100,
        max=2000,
        step=10,
        value=700,
        description="filter_base",
    )
    filter_range = FloatSlider(
        min=0,
        max=1500,
        step=10,
        value=600,
        description="filter_range",
    )
    reverb_size = FloatSlider(
        min=0,
        max=1,
        step=0.05,
        value=0.8,
        description="reverb_size",
    )
    reverb_damp = FloatSlider(
        min=0,
        max=1,
        step=0.05,
        value=0.5,
        description="reverb_damp",
    )
    reverb_bal = FloatSlider(
        min=0,
        max=1,
        step=0.05,
        value=0.75,
        description="reverb_bal",
    )
    delay_time = FloatSlider(
        min=0.05,
        max=2,
        step=0.05,
        value=0.45,
        description="delay_time",
    )
    delay_feedback = FloatSlider(
        min=0,
        max=0.9,
        step=0.05,
        value=0.3,
        description="delay_feedback",
    )
    volume = FloatSlider(
        min=0,
        max=2,
        step=0.1,
        value=0.6,
        description="volume",
    )

    controls = {
        "enabled": enabled,
        "root_freq": root_freq,
        "cutoff_speed": cutoff_speed,
        "cutoff_chaos": cutoff_chaos,
        "filter_res": filter_res,
        "filter_base": filter_base,
        "filter_range": filter_range,
        "reverb_size": reverb_size,
        "reverb_damp": reverb_damp,
        "reverb_bal": reverb_bal,
        "delay_time": delay_time,
        "delay_feedback": delay_feedback,
        "volume": volume,
    }
    if controller is not None:
        controller.register(
            "soundscape_filter",
            controls,
            lambda: set_params(**{name: widget.value for name, widget in controls.items()}),
        )

    output = interactive_output(set_params, controls)
    slider_rows = [
        HBox([root_freq, HTML("Fundamental frequency of the static harmonic tone.")]),
        HBox(
            [
                cutoff_speed,
                HTML("How fast the filter cutoff wanders - lower is slower and more spacious."),
            ]
        ),
        HBox(
            [
                cutoff_chaos,
                HTML("How unpredictable the sweep is - higher is more angular and psychedelic."),
            ]
        ),
        HBox([filter_res, HTML("Filter resonance - higher gives a more vocal, wah-like sweep.")]),
        HBox([filter_base, HTML("Center cutoff the sweep rides on - higher is brighter.")]),
        HBox([filter_range, HTML("How far the cutoff sweeps - larger is more dramatic.")]),
        HBox([reverb_size, HTML("Reverb room size - larger is more enveloping.")]),
        HBox([reverb_damp, HTML("Reverb high-frequency damping - higher is darker.")]),
        HBox([reverb_bal, HTML("Reverb dry/wet balance - 0 is dry and 1 is wet.")]),
        HBox([delay_time, HTML("Delay time - smears the filter sweep across time.")]),
        HBox(
            [
                delay_feedback,
                HTML("Delay feedback - higher repeats echoes more times before decaying."),
            ]
        ),
        HBox([volume, HTML("Output level for this patch, limited so it won't clip.")]),
    ]
    return VBox([enabled, *slider_rows, output])
    """
