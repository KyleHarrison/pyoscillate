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
from collections.abc import Callable
from typing import ClassVar

from pyo import PyoObject
from pyo.lib._core import Mix, Sig
from pyo.lib.filters import Biquad
from pyo.lib.generators import FM, Noise, Sine
from pyo.lib.triggers import TrigEnv

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.patches.base import Patch
from pyoscillate.patches.drums.base import DrumVoice
from pyoscillate.patches.params import Param, rate_param
from pyoscillate.tempo import Tempo

# carrier (Hz), modulator ratio, index
METAL_OPERATORS = (
    (3100.0, 1.41, 5.0),
    (4700.0, 1.73, 4.0),
    (6200.0, 1.29, 4.0),
    (8300.0, 1.87, 3.0),
)
# full-to-zero break-points for the amplitude envelope
DROP = [(0, 1), (8191, 0)]


class Cymbal(DrumVoice):
    """Ride/crash cymbal: dense metallic source through a resonant
    band-pass with a slow, tempo-locked drift of the band's centre. Style
    variants share this graph and override the profile attributes below."""

    volume_default = 0.15
    base_division: ClassVar[NoteDivision] = NoteDivision.SIXTEENTH
    noise_level: ClassVar[float] = 0.3
    # one full drift of the band centre spans this many bars
    movement_bars: ClassVar[int] = 4
    # a constant-Q band-pass passes more energy the higher it's centred; this
    # keeps loudness steady as Brightness moves (see `_makeup`)
    makeup_gain: ClassVar[float] = 2.0
    reference_tone: ClassVar[float] = 7000
    decay_curve: ClassVar[float] = 3

    # cycle length in 16th steps, step -> accent within that cycle, decay
    # (s), band-pass resonance - overridden per style
    cycle: ClassVar[int]
    pattern: ClassVar[dict[int, float]]
    decay: ClassVar[float]
    resonance: ClassVar[float]

    # the graph, assigned by build(); finish() retains every one of them
    operators: tuple[FM, ...]
    noise: Noise
    source: PyoObject
    amp_env: TrigEnv
    shaped: PyoObject
    centre: Sig
    drift: Sine
    band: PyoObject
    tone_filter: Biquad

    # the step pattern's callable, frozen at build time - fed to
    # `next_step`, which build() can no longer close over now that it's a
    # real method
    _step: Callable[[], tuple[int, float | None]]

    @Param(
        0.02,
        0.4,
        0.01,
        0.1,
        "Presence",
        "Sets how far forward the cymbal sits; keep it low so the tail doesn't mask the groove.",
    )
    def level(self, value: float) -> None:
        self.amp_env.mul = value

    @Param(
        3000,
        12000,
        100,
        7000,
        "Brightness",
        "Moves the cymbal from a darker, washier body (lower) to a thinner, more glassy shimmer (higher).",
    )
    def tone(self, value: float) -> None:
        self.centre.value = value
        self.tone_filter.mul = self._makeup(value)

    @Param(
        0.5,
        2.0,
        0.05,
        1.0,
        "Length",
        "Shortens the cymbal toward a tighter, controlled hit or lets the tail hang and dissolve for longer.",
    )
    def length(self, value: float) -> None:
        self.amp_env.dur = self.decay * value

    @Param(
        0.0,
        0.3,
        0.01,
        0.1,
        "Movement",
        "How much the cymbal's colour drifts from strike to strike; none is static and repetitive, more "
        "keeps a repeated pattern alive.",
    )
    def movement(self, value: float) -> None:
        self.drift.mul = value

    rate = rate_param(
        base_division,
        "Halves or doubles the cymbal pattern speed for each step away from its 16th-note grid.",
    )

    def _makeup(self, tone: float) -> float:
        return self.makeup_gain * math.sqrt(self.reference_tone / tone)

    def build(self, tempo: Tempo, clock: Clock) -> Patch:
        """Build a ride or crash cymbal with slow strike-to-strike colour drift."""
        self._reset()

        self.operators = tuple(
            FM(carrier=carrier, ratio=ratio, index=index, mul=1 / len(METAL_OPERATORS))
            for carrier, ratio, index in METAL_OPERATORS
        )
        self.noise = Noise(mul=self.noise_level)
        self.source = Mix([*self.operators, self.noise], voices=1)
        self.amp_env = self.envelope(
            DROP, dur=self.decay * self.length, mul=self.level, exp=self.decay_curve
        )
        self.shaped = self.source * self.amp_env

        self.centre = Sig(self.tone)
        self.drift = Sine(freq=1 / (self.movement_bars * tempo.bar), mul=self.movement, add=1)
        self.band = self.centre * self.drift
        self.tone_filter = Biquad(
            self.shaped, freq=self.band, q=self.resonance, type=2, mul=self._makeup(self.tone)
        )

        self._step = self.step_pattern(self.cycle, self.pattern)

        self.schedule(self.base_division, self.rate, clock)
        return self.finish(self.tone_filter)

    def next_step(self) -> None:
        _, accent = self._step()
        if accent is not None:
            self.amp_env.mul = self.level * accent
            self.trigger.play()


class CymbalRide(Cymbal):
    """Quarter-note ride with slowly drifting metallic colour."""

    cycle, pattern, decay, resonance = 16, {0: 1.0, 4: 0.8, 8: 0.9, 12: 0.8}, 1.0, 3.0


class CymbalCrash(Cymbal):
    """Long crash wash marking the start of every eight-bar phrase."""

    cycle, pattern, decay, resonance = 128, {0: 1.0}, 2.6, 1.2
