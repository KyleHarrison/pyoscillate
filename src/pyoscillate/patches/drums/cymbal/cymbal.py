# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.drums.cymbal.cymbal style=ride
#   style: ride | crash
"""Ride and crash cymbal voices.

A dense metallic source - high FM operators at inharmonic ratios with a little
noise for diffusion - runs through a resonant band-pass and a long exponential
envelope. A slow, tempo-locked drift of the band's centre makes successive
strikes differ slightly. The ride keeps quarter-note top-end motion; the crash
marks the start of each eight-bar phrase with a long, broad wash.
"""

import math
from typing import Any, ClassVar

from pyo.lib._core import Mix, Sig
from pyo.lib.filters import Biquad
from pyo.lib.generators import FM, Noise, Sine

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.patches.base import Patch
from pyoscillate.patches.drums.base import DrumVoice
from pyoscillate.patches.params import SliderSpec, rate_slider
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
    rate_slider(
        BASE_DIVISION,
        "Halves or doubles the cymbal pattern speed for each step away from its 16th-note grid.",
    ),
)
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


class Cymbal(DrumVoice):
    """Ride/crash cymbal: dense metallic source through a resonant
    band-pass with a slow, tempo-locked drift of the band's centre. Style
    variants share this graph and override the profile attributes below."""

    parameters = PARAMETERS
    volume_default = VOLUME_DEFAULT

    level: float
    tone: float
    length: float
    movement: float
    rate: float

    # cycle length in 16th steps, step -> accent within that cycle, decay
    # (s), band-pass resonance - overridden per style
    cycle: ClassVar[int]
    pattern: ClassVar[dict[int, float]]
    decay: ClassVar[float]
    resonance: ClassVar[float]

    def build(self, tempo: Tempo, clock: Clock, **values: Any) -> Patch:
        """Build a ride or crash cymbal with slow strike-to-strike colour drift."""
        self.configure(**values)
        self._reset()
        operators = tuple(
            FM(carrier=carrier, ratio=ratio, index=index, mul=1 / len(METAL_OPERATORS))
            for carrier, ratio, index in METAL_OPERATORS
        )
        noise = Noise(mul=NOISE_LEVEL)
        source = Mix([*operators, noise], voices=1)
        envelope = self.envelope(
            [(0, 1), (8191, 0)], dur=self.decay * self.length, mul=self.level, exp=DECAY_CURVE
        )
        shaped = source * envelope

        centre = Sig(self.tone)
        drift = Sine(freq=1 / (MOVEMENT_BARS * tempo.bar), mul=self.movement, add=1)
        band = centre * drift
        voice = Biquad(shaped, freq=band, q=self.resonance, type=2, mul=_makeup(self.tone))
        self.retain(*operators, noise, source, shaped, centre, drift, band)
        state = {"level": self.level}

        step = self.step_pattern(self.cycle, self.pattern)

        def next_step() -> None:
            _, accent = step()
            if accent is not None:
                envelope.mul = state["level"] * accent
                self.trigger.play()

        def set_level(value: float) -> None:
            state["level"] = value
            envelope.mul = value

        def set_tone(value: float) -> None:
            centre.value = value
            voice.mul = _makeup(value)

        self.schedule(BASE_DIVISION, self.rate, clock, next_step)
        return self.finish(
            voice,
            {
                "level": set_level,
                "tone": set_tone,
                "length": lambda value: setattr(envelope, "dur", self.decay * value),
                "movement": lambda value: setattr(drift, "mul", value),
            },
        )


class CymbalRide(Cymbal):
    """Quarter-note ride with slowly drifting metallic colour."""

    cycle, pattern, decay, resonance = 16, {0: 1.0, 4: 0.8, 8: 0.9, 12: 0.8}, 1.0, 3.0


class CymbalCrash(Cymbal):
    """Long crash wash marking the start of every eight-bar phrase."""

    cycle, pattern, decay, resonance = 128, {0: 1.0}, 2.6, 1.2
