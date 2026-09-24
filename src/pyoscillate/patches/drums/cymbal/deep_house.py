"""Cymbal voices for the Deep House project.

A dense metallic source - high FM operators at inharmonic ratios with a little
noise for diffusion - runs through a resonant band-pass and a long exponential
envelope. A slow, tempo-locked drift of the band's centre makes successive
strikes differ slightly. The ride keeps quarter-note top-end motion; the crash
marks the start of each eight-bar phrase with a long, broad wash.
"""

import math
from collections.abc import Callable

from ipywidgets import VBox
from pyo.lib._core import Mix, Sig
from pyo.lib.filters import Biquad
from pyo.lib.generators import FM, Noise, Sine
from pyo.lib.tables import ExpTable
from pyo.lib.triggers import Trig, TrigEnv

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.patches.base import Patch, PatchRack
from pyoscillate.patches.presets import PresetController
from pyoscillate.patches.widgets import SliderSpec, patch_widget
from pyoscillate.tempo import Tempo

BASE_DIVISION = NoteDivision.SIXTEENTH

PARAMETERS = (
    SliderSpec(
        "level",
        0.02,
        0.4,
        0.01,
        0.1,
        "Presence",
        "Sets how far forward the cymbal sits; keep it low so the tail doesn't mask the groove.",
    ),
    SliderSpec(
        "tone",
        3000,
        12000,
        100,
        7000,
        "Brightness",
        "Moves the cymbal from a darker, washier body (lower) to a thinner, more glassy shimmer (higher).",
    ),
    SliderSpec(
        "length",
        0.5,
        2.0,
        0.05,
        1.0,
        "Length",
        "Shortens the cymbal toward a tighter, controlled hit or lets the tail hang and dissolve for longer.",
    ),
    SliderSpec(
        "movement",
        0.0,
        0.3,
        0.01,
        0.1,
        "Movement",
        "How much the cymbal's colour drifts from strike to strike; none is static and repetitive, more "
        "keeps a repeated pattern alive.",
    ),
    SliderSpec(
        "rate",
        Clock.rate_limits(BASE_DIVISION)[0],
        Clock.rate_limits(BASE_DIVISION)[1],
        1,
        0,
        "Rate",
        "Halves or doubles the cymbal pattern speed for each step away from its 16th-note grid.",
    ),
)
# cycle length in 16th steps, and step -> accent within that cycle
PATTERNS = {
    "ride": (16, {0: 1.0, 4: 0.8, 8: 0.9, 12: 0.8}),
    "crash": (128, {0: 1.0}),
}
# decay (s), band-pass resonance - the ride rings in a focused band, the
# crash spreads broadly and hangs much longer
PROFILES = {
    "ride": (1.0, 3.0),
    "crash": (2.6, 1.2),
}
# carrier (Hz), modulator ratio, index
METAL_OPERATORS = (
    (3100.0, 1.41, 5.0),
    (4700.0, 1.73, 4.0),
    (6200.0, 1.29, 4.0),
    (8300.0, 1.87, 3.0),
)
NOISE_LEVEL = 0.3
# one full drift of the band centre spans this many bars
MOVEMENT_BARS = 4
# a constant-Q band-pass passes more energy the higher it's centred; this
# keeps loudness steady as Brightness moves (see `_makeup`)
MAKEUP_GAIN = 2.0
REFERENCE_TONE = 7000
DECAY_CURVE = 3
VOLUME_DEFAULT = 0.15


def _makeup(tone: float) -> float:
    return MAKEUP_GAIN * math.sqrt(REFERENCE_TONE / tone)


def build(
    tempo: Tempo,
    clock: Clock,
    style: str,
    level: float = 0.1,
    tone: float = 7000,
    length: float = 1.0,
    movement: float = 0.1,
    rate: float = 0,
) -> Patch:
    """Build a ride or crash cymbal with slow strike-to-strike colour drift."""
    cycle, pattern = PATTERNS[style]
    decay, resonance = PROFILES[style]
    trigger = Trig()

    operators = tuple(
        FM(carrier=carrier, ratio=ratio, index=index, mul=1 / len(METAL_OPERATORS))
        for carrier, ratio, index in METAL_OPERATORS
    )
    noise = Noise(mul=NOISE_LEVEL)
    source = Mix([*operators, noise], voices=1)
    envelope_table = ExpTable([(0, 1), (8191, 0)], exp=DECAY_CURVE)
    envelope = TrigEnv(trigger, envelope_table, dur=decay * length, mul=level)
    shaped = source * envelope

    centre = Sig(tone)
    drift = Sine(freq=1 / (MOVEMENT_BARS * tempo.bar), mul=movement, add=1)
    band = centre * drift
    voice = Biquad(shaped, freq=band, q=resonance, type=2, mul=_makeup(tone))
    state = {"step": 0, "level": level}

    def next_step() -> None:
        accent = pattern.get(state["step"] % cycle)
        if accent is not None:
            envelope.mul = state["level"] * accent
            trigger.play()
        state["step"] += 1

    def set_level(value: float) -> None:
        state["level"] = value
        envelope.mul = value

    def set_tone(value: float) -> None:
        centre.value = value
        voice.mul = _makeup(value)

    division = clock.subscribe(clock.ticks_for_rate(BASE_DIVISION, rate), next_step)
    return Patch(
        sequencer=division,
        voice=voice,
        controls={
            "level": set_level,
            "tone": set_tone,
            "length": lambda value: setattr(envelope, "dur", decay * value),
            "movement": lambda value: setattr(drift, "mul", value),
            "rate": lambda value: setattr(
                division, "steps", clock.ticks_for_rate(BASE_DIVISION, value)
            ),
        },
        resources=(
            trigger,
            *operators,
            noise,
            source,
            envelope_table,
            envelope,
            shaped,
            centre,
            drift,
            band,
        ),
    )


def make_builder(style: str) -> Callable[..., Patch]:
    """Return a builder with one cymbal style fixed for a rack entry."""
    return lambda tempo, clock, **values: build(tempo, clock, style, **values)


def widget(
    rack: PatchRack,
    tempo: Tempo,
    clock: Clock,
    controller: PresetController | None = None,
    style: str = "ride",
) -> VBox:
    """Create controls for one cymbal style."""
    return patch_widget(
        rack,
        f"cymbal_{style}",
        make_builder(style),
        PARAMETERS,
        controller=controller,
        volume_default=VOLUME_DEFAULT,
        build_kwargs={"tempo": tempo, "clock": clock},
    )
