from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

from ipywidgets import VBox
from pyo.lib.effects import Freeverb
from pyo.lib.generators import FM
from pyo.lib.tables import CosTable
from pyo.lib.triggers import Metro, TrigEnv, TrigFunc

from pyoscillate.patches.base import Patch, PatchRack
from pyoscillate.patches.presets import PresetController
from pyoscillate.patches.widgets import PyoParamRef, SliderSpec, patch_widget

# major pentatonic across one octave - consonant, calm, no leading tones
CANON_SCALE = [0, 2, 4, 7, 9, 12]

CANON_ROOT = 220  # A3, current notebook default

PARAMETERS = (
    SliderSpec(
        "root_freq",
        110,
        440,
        1,
        CANON_ROOT,
        "Root frequency",
        "Voice A root.",
        (PyoParamRef(FM, "carrier"),),
    ),
    SliderSpec(
        "voice_a_period",
        1,
        12,
        0.5,
        5.0,
        "Voice A period",
        "Seconds between draws; rebuilds the Metro.",
        (),
    ),
    SliderSpec(
        "voice_b_period",
        1,
        12,
        0.5,
        7.5,
        "Voice B period",
        "Seconds between draws; rebuilds the Metro.",
        (),
    ),
    SliderSpec(
        "voice_b_interval",
        0,
        12,
        1,
        7,
        "Voice B interval",
        "Voice B register offset.",
        (),
    ),
    SliderSpec(
        "note_duration",
        0.5,
        10,
        0.5,
        4.0,
        "Note duration",
        "Envelope duration; rebuilds envelopes.",
        (PyoParamRef(TrigEnv, "dur"),),
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
        0.7,
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
        0.5,
        "Reverb balance",
        "Dry/wet balance.",
        (PyoParamRef(Freeverb, "bal"),),
    ),
)


@dataclass(eq=False)
class _Duet:
    """Wraps the two independently-timed, free-running `Metro`s driving each
    voice's note changes, plus strong references to their `TrigFunc`
    callbacks - see `clock_tick.py`'s `_Clocks` docstring for why this
    keepalive matters alongside another `Pattern`-driven callback.
    """

    metros: list[Metro]
    keepalive: list[Any] = field(default_factory=list)

    def play(self) -> None:
        for metro in self.metros:
            metro.play()

    def stop(self) -> None:
        for metro in self.metros:
            metro.stop()


def build(
    root_freq: float = CANON_ROOT,
    voice_a_period: float = 5.0,
    voice_b_period: float = 7.5,
    voice_b_interval: float = 7,
    note_duration: float = 4.0,
    fm_ratio: float = 1.5,
    fm_index: float = 1.5,
    reverb_size: float = 0.7,
    reverb_damp: float = 0.5,
    reverb_bal: float = 0.5,
) -> Patch:
    """Two-voice generative canon: a pair of melodic voices, each drawing random pentatonic notes on
    its own free-running period, so they drift in and out of alignment like an ever-shifting call and
    response.

    Both voices draw from the same scale, so they always stay consonant
    with each other, but their unrelated (non-integer-ratio) periods mean
    they rarely repeat the same relationship to one another - the "canon"
    quality comes from that drift, not from one voice literally echoing
    the other.

    Args:
        root_freq: Base frequency (Hz) for voice A. Voice B sits
            `voice_b_interval` semitones above it.
        voice_a_period: Seconds between voice A's random note draws.
        voice_b_period: Seconds between voice B's random note draws.
            Deliberately not a simple multiple of `voice_a_period`, so the
            two voices' note changes drift past each other over time
            instead of ever locking into a fixed pattern.
        voice_b_interval: Semitone offset of voice B's register above
            `root_freq`. A fifth (7) or fourth (5) keeps a clear harmonic
            relationship between the two voices; an octave (12) keeps them
            in the same register class further apart in pitch space.
        note_duration: How long each note's envelope sustains, in seconds.
            Longer than either period lets notes overlap into each other
            for a smoother, more legato feel.
        fm_ratio: Modulator/carrier ratio in the FM voice, shared by both
            voices. Values close to a simple ratio (1, 1.5, 2) sound clean
            and bell-like.
        fm_index: FM modulation index, shared by both voices - how
            bright/buzzy the timbre is. Kept low by default so both voices
            stay soft and rounded.
        reverb_size: Freeverb room size (0-1), applied to the summed duet.
        reverb_damp: Freeverb high-frequency damping (0-1).
        reverb_bal: Freeverb dry/wet balance (0-1).
    """
    envelope_table = CosTable([(0, 0), (800, 1), (4000, 0.5), (8191, 0)])

    voice_a_metro = Metro(time=voice_a_period)
    voice_a_env = TrigEnv(
        voice_a_metro, table=envelope_table, dur=note_duration, mul=0.18
    )
    voice_a_fm = FM(carrier=root_freq, ratio=fm_ratio, index=fm_index, mul=voice_a_env)

    voice_b_root = root_freq * pow(2, voice_b_interval / 12)
    voice_b_metro = Metro(time=voice_b_period)
    voice_b_env = TrigEnv(
        voice_b_metro, table=envelope_table, dur=note_duration, mul=0.14
    )
    voice_b_fm = FM(
        carrier=voice_b_root, ratio=fm_ratio, index=fm_index, mul=voice_b_env
    )

    voice = Freeverb(
        voice_a_fm + voice_b_fm, size=reverb_size, damp=reverb_damp, bal=reverb_bal
    )

    def next_voice_a() -> None:
        interval = random.choice(CANON_SCALE)
        voice_a_fm.carrier = root_freq * pow(2, interval / 12)

    def next_voice_b() -> None:
        interval = random.choice(CANON_SCALE)
        voice_b_fm.carrier = voice_b_root * pow(2, interval / 12)

    voice_a_func = TrigFunc(voice_a_metro, next_voice_a)
    voice_b_func = TrigFunc(voice_b_metro, next_voice_b)

    sequencer = _Duet(
        metros=[voice_a_metro, voice_b_metro],
        keepalive=[
            envelope_table,
            voice_a_env,
            voice_b_env,
            voice_a_func,
            voice_b_func,
        ],
    )
    return Patch(
        sequencer=sequencer,
        voice=voice,
        controls={
            "root_freq": lambda value: setattr(voice_a_fm, "carrier", value),
            "fm_ratio": lambda value: (
                setattr(voice_a_fm, "ratio", value),
                setattr(voice_b_fm, "ratio", value),
            ),
            "fm_index": lambda value: (
                setattr(voice_a_fm, "index", value),
                setattr(voice_b_fm, "index", value),
            ),
            "reverb_size": lambda value: setattr(voice, "size", value),
            "reverb_damp": lambda value: setattr(voice, "damp", value),
            "reverb_bal": lambda value: setattr(voice, "bal", value),
        },
    )


def widget(rack: PatchRack, controller: PresetController | None = None) -> VBox:
    """Create mid_canon controls."""
    return patch_widget(
        rack,
        "mid_canon",
        build,
        PARAMETERS,
        controller=controller,
        rebuild_parameters=(
            "voice_a_period",
            "voice_b_period",
            "voice_b_interval",
            "note_duration",
        ),
    )

    """

    def set_params(
        enabled,
        root_freq,
        voice_a_period,
        voice_b_period,
        voice_b_interval,
        note_duration,
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
            rack.stop("mid_canon")
            return

        patch = build(
            root_freq,
            voice_a_period,
            voice_b_period,
            voice_b_interval,
            note_duration,
            fm_ratio,
            fm_index,
            reverb_size,
            reverb_damp,
            reverb_bal,
        )
        patch.volume = volume
        rack.start("mid_canon", patch)

    enabled = Checkbox(value=False, description="mid_canon on/off")
    root_freq = FloatSlider(min=110, max=440, step=1, value=CANON_ROOT, description="root_freq")
    voice_a_period = FloatSlider(min=1, max=12, step=0.5, value=5.0, description="voice_a_period")
    voice_b_period = FloatSlider(min=1, max=12, step=0.5, value=7.5, description="voice_b_period")
    voice_b_interval = FloatSlider(min=0, max=12, step=1, value=7, description="voice_b_interval")
    note_duration = FloatSlider(min=0.5, max=10, step=0.5, value=4.0, description="note_duration")
    fm_ratio = FloatSlider(min=0.5, max=4, step=0.1, value=1.5, description="fm_ratio")
    fm_index = FloatSlider(min=0, max=6, step=0.1, value=1.5, description="fm_index")
    reverb_size = FloatSlider(min=0, max=1, step=0.05, value=0.7, description="reverb_size")
    reverb_damp = FloatSlider(min=0, max=1, step=0.05, value=0.5, description="reverb_damp")
    reverb_bal = FloatSlider(min=0, max=1, step=0.05, value=0.5, description="reverb_bal")
    volume = FloatSlider(min=0, max=2, step=0.1, value=0.6, description="volume")

    controls = {
        "enabled": enabled,
        "root_freq": root_freq,
        "voice_a_period": voice_a_period,
        "voice_b_period": voice_b_period,
        "voice_b_interval": voice_b_interval,
        "note_duration": note_duration,
        "fm_ratio": fm_ratio,
        "fm_index": fm_index,
        "reverb_size": reverb_size,
        "reverb_damp": reverb_damp,
        "reverb_bal": reverb_bal,
        "volume": volume,
    }
    if controller is not None:
        controller.register(
            "mid_canon",
            controls,
            lambda: set_params(**{name: widget.value for name, widget in controls.items()}),
        )

    output = interactive_output(set_params, controls)
    slider_rows = [
        HBox([root_freq, HTML("Base frequency for voice A; voice B sits above it.")]),
        HBox([voice_a_period, HTML("Seconds between voice A's random note draws.")]),
        HBox([voice_b_period, HTML("Seconds between voice B's random note draws.")]),
        HBox([voice_b_interval, HTML("Semitones voice B sits above voice A.")]),
        HBox(
            [
                note_duration,
                HTML("How long each note sustains - longer overlaps into a legato feel."),
            ]
        ),
        HBox(
            [fm_ratio, HTML("Modulator/carrier ratio - controls harmonic versus dissonant tone.")]
        ),
        HBox([fm_index, HTML("FM modulation depth - higher is brighter and buzzier.")]),
        HBox([reverb_size, HTML("Reverb room size - larger is more distant.")]),
        HBox([reverb_damp, HTML("Reverb high-frequency damping - higher is darker.")]),
        HBox([reverb_bal, HTML("Reverb dry/wet balance - 0 is dry and 1 is wet.")]),
        HBox([volume, HTML("Output level for this patch, limited so it won't clip.")]),
    ]
    return VBox([enabled, *slider_rows, output])
    """
