from __future__ import annotations

from ipywidgets import VBox
from pyo.lib.controls import SigTo
from pyo.lib.effects import Freeverb
from pyo.lib.generators import FM

from pyoscillate.clock import BAR, Clock
from pyoscillate.patches.base import Patch, PatchRack
from pyoscillate.patches.presets import PresetController
from pyoscillate.patches.widgets import PyoParamRef, SliderSpec, patch_widget
from pyoscillate.tempo import Tempo

# major pentatonic - consonant, calm, no leading tones to create tension
MID_INTERVALS = [0, 2, 4, 7, 9, 12, 9, 7, 4, 2]

MID_ROOT = 330  # E4, current notebook default

PARAMETERS = (
    SliderSpec(
        "root_freq",
        110,
        660,
        1,
        MID_ROOT,
        "Root frequency",
        "Melody root.",
        (PyoParamRef(FM, "carrier"),),
    ),
    SliderSpec(
        "step_bars",
        1,
        8,
        1,
        2,
        "Step bars",
        "Bars between notes; changing it rebuilds the clock subscription.",
        (),
    ),
    SliderSpec(
        "fm_ratio",
        0.5,
        4,
        0.1,
        1.5,
        "FM ratio",
        "Carrier/modulator ratio.",
        (PyoParamRef(FM, "ratio"),),
    ),
    SliderSpec(
        "fm_index",
        0,
        6,
        0.1,
        1.5,
        "FM index",
        "FM brightness.",
        (PyoParamRef(FM, "index"),),
    ),
    SliderSpec(
        "reverb_size",
        0,
        1,
        0.05,
        0.6,
        "Reverb size",
        "Room size.",
        (PyoParamRef(Freeverb, "size"),),
    ),
    SliderSpec(
        "reverb_damp",
        0,
        1,
        0.05,
        0.5,
        "Reverb damping",
        "Damping.",
        (PyoParamRef(Freeverb, "damp"),),
    ),
    SliderSpec(
        "reverb_bal",
        0,
        1,
        0.05,
        0.4,
        "Reverb balance",
        "Dry/wet balance.",
        (PyoParamRef(Freeverb, "bal"),),
    ),
)


def build(
    tempo: Tempo,
    clock: Clock,
    root_freq: float = MID_ROOT,
    step_bars: int = 2,
    fm_ratio: float = 1.5,
    fm_index: float = 1.5,
    reverb_size: float = 0.6,
    reverb_damp: float = 0.5,
    reverb_bal: float = 0.4,
) -> Patch:
    """Slow, fixed pentatonic arpeggio locked to the shared clock, gliding between notes rather than plucking them.

    Args:
        tempo: Shared tempo grid; unused directly here beyond being passed
            through to `clock`, but kept in the signature to match every
            other clocked patch's `build(tempo, clock, ...)` shape.
        clock: Shared master pulse; the melody steps every `step_bars`
            bars, phase-locked to every other patch on the clock.
        root_freq: Base frequency (Hz) of the melody's root note, before
            the `MID_INTERVALS` offsets are applied each step. Raising it
            brings the melody closer to a lead register and easier to pick
            out; lowering it moves it toward the drone/atmosphere register
            and lets it blend in more as a background element.
        step_bars: How many bars pass between melody notes. Larger values
            space the notes further apart for a calmer, more spacious
            melody; smaller values make it read as more active and
            foreground.
        fm_ratio: Modulator/carrier ratio in the FM voice. Values close to a
            simple ratio (1, 1.5, 2) sound clean and bell-like; the default
            gives a calm, consonant timbre appropriate for a background
            mid voice.
        fm_index: FM modulation index - how bright/buzzy the timbre is.
            Kept low by default so the voice stays soft and rounded rather
            than cutting through the mix.
        reverb_size: Freeverb room size (0-1). Moderate by default - present
            enough to sit clearly in the stereo field without dissolving
            into the background as much as the drone/soundscape layers do.
        reverb_damp: Freeverb high-frequency damping (0-1).
        reverb_bal: Freeverb dry/wet balance (0-1). Lower than the
            soundscape patches by default, so the melodic line stays
            legible rather than fully diffused.
    """
    step_time = tempo.bar * step_bars

    # glides to each new note over most of the step time instead of snapping,
    # so the melody drifts between pitches rather than plucking them
    mid_freq = SigTo(value=root_freq, time=step_time * 0.85)

    fm_voice = FM(carrier=mid_freq, ratio=fm_ratio, index=fm_index, mul=0.18)
    voice = Freeverb(fm_voice, size=reverb_size, damp=reverb_damp, bal=reverb_bal)

    step = {"i": 0}

    def next_step() -> None:
        i = step["i"] % len(MID_INTERVALS)
        mid_freq.value = root_freq * pow(2, MID_INTERVALS[i] / 12)
        step["i"] += 1

    sequencer = clock.subscribe(BAR * step_bars, next_step)
    return Patch(
        sequencer=sequencer,
        voice=voice,
        controls={
            "root_freq": lambda value: setattr(mid_freq, "value", value),
            "fm_ratio": lambda value: setattr(fm_voice, "ratio", value),
            "fm_index": lambda value: setattr(fm_voice, "index", value),
            "reverb_size": lambda value: setattr(voice, "size", value),
            "reverb_damp": lambda value: setattr(voice, "damp", value),
            "reverb_bal": lambda value: setattr(voice, "bal", value),
        },
    )


def widget(
    rack: PatchRack,
    tempo: Tempo,
    clock: Clock,
    controller: PresetController | None = None,
) -> VBox:
    """Create mid_arp controls."""
    return patch_widget(
        rack,
        "mid_arp",
        build,
        PARAMETERS,
        controller=controller,
        rebuild_parameters=("step_bars",),
        build_kwargs={"tempo": tempo, "clock": clock},
    )

    """

    def set_params(
        enabled,
        root_freq,
        step_bars,
        fm_ratio,
        fm_index,
        reverb_size,
        reverb_damp,
        reverb_bal,
        volume,
    ):
        if controller is not None and controller.applying:
            return
        if not enabled:
            rack.stop("mid_arp")
            return

        patch = build(
            tempo,
            clock,
            root_freq,
            step_bars,
            fm_ratio,
            fm_index,
            reverb_size,
            reverb_damp,
            reverb_bal,
        )
        patch.volume = volume
        rack.start("mid_arp", patch)

    enabled = Checkbox(value=False, description="mid_arp on/off")
    root_freq = FloatSlider(
        min=110,
        max=660,
        step=1,
        value=MID_ROOT,
        description="root_freq",
    )
    step_bars = IntSlider(min=1, max=8, step=1, value=2, description="step_bars")
    fm_ratio = FloatSlider(
        min=0.5,
        max=4,
        step=0.1,
        value=1.5,
        description="fm_ratio",
    )
    fm_index = FloatSlider(
        min=0,
        max=6,
        step=0.1,
        value=1.5,
        description="fm_index",
    )
    reverb_size = FloatSlider(
        min=0,
        max=1,
        step=0.05,
        value=0.6,
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
        value=0.4,
        description="reverb_bal",
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
        "step_bars": step_bars,
        "fm_ratio": fm_ratio,
        "fm_index": fm_index,
        "reverb_size": reverb_size,
        "reverb_damp": reverb_damp,
        "reverb_bal": reverb_bal,
        "volume": volume,
    }
    if controller is not None:
        controller.register(
            "mid_arp",
            controls,
            lambda: set_params(**{name: widget.value for name, widget in controls.items()}),
        )

    output = interactive_output(set_params, controls)
    slider_rows = [
        HBox([root_freq, HTML("Base frequency of the melody's root note.")]),
        HBox(
            [
                step_bars,
                HTML("How many bars between melody notes - larger is calmer and slower."),
            ]
        ),
        HBox(
            [
                fm_ratio,
                HTML("Modulator/carrier ratio - controls harmonic versus dissonant tone."),
            ]
        ),
        HBox([fm_index, HTML("FM modulation depth - higher is brighter and buzzier.")]),
        HBox([reverb_size, HTML("Reverb room size - larger is more distant.")]),
        HBox([reverb_damp, HTML("Reverb high-frequency damping - higher is darker.")]),
        HBox([reverb_bal, HTML("Reverb dry/wet balance - 0 is dry and 1 is wet.")]),
        HBox([volume, HTML("Output level for this patch, limited so it won't clip.")]),
    ]
    return VBox([enabled, *slider_rows, output])
    """
