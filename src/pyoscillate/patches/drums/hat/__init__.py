# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.drums.hat
"""Subtle high-passed noise tick, once per 8th note, for top-end texture.

A short noise burst is shaped by a fast exponential decay, slowly swelled in
level over 32 steps so the ticks don't sit at a fixed level, and high-passed
to keep it thin and airy, out of the kick and bass range.
"""

from typing import ClassVar

from pyo import PyoObject
from pyo.lib.filters import ButHP
from pyo.lib.generators import Noise, Sine
from pyo.lib.triggers import TrigEnv

from pyoscillate.clock import NoteDivision
from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.drums.base import DrumVoice
from pyoscillate.patches.params import Param, rate_param

# full-to-zero break-points shared by the tick's envelope
DROP = [(0, 1), (8191, 0)]
# the tick's own default decay (s); read directly at construction (as well as
# from its own `@Param`) since there's no separate style constant behind it
DECAY = 0.15
CUTOFF_FREQ = 10300


class Tick(DrumVoice):
    """Subtle high-passed noise tick, once per 8th note, for top-end texture."""

    name = "hat"
    title = "Hi-hat"
    summary = "Subtle, airy top-end pulse."
    volume = Patch.volume.replace(default=0.2)
    base_division: ClassVar[NoteDivision] = NoteDivision.EIGHTH
    # exponent of the decay curve - a sharp, strongly exponential drop keeps
    # the hat ticking rather than hissing
    decay_curve: ClassVar[float] = 5

    # the graph, assigned by build(); finish() retains every one of them
    hat_noise: Noise
    hat_env: TrigEnv
    hat_burst: PyoObject
    hat_swell: Sine
    filtered: ButHP

    @Param(
        2000,
        12000,
        100,
        CUTOFF_FREQ,
        "Brightness",
        "Moves the tick from fuller and more present (lower) to thinner, airier, and more distant-sounding "
        "(higher).",
    )
    def cutoff_freq(self, value: float) -> None:
        self.filtered.freq = value

    @Param(
        0,
        1,
        0.05,
        0.2,
        "Presence",
        "Sets how upfront the tick sits in the mix, from a subtle texture to a louder, more foregrounded pulse.",
    )
    def level(self, value: float) -> None:
        self.hat_env.mul = value

    @Param(
        0.03,
        0.6,
        0.01,
        DECAY,
        "Tightness",
        "Shapes the tick's tail; shorter feels tight and click-like, longer blurs into more of a hiss.",
    )
    def decay(self, value: float) -> None:
        self.hat_env.dur = value

    rate = rate_param(
        base_division,
        "Halves or doubles the tick pattern speed for each step away from its 8th-note grid.",
    )

    def build(self, context: BuildContext) -> Patch:
        """Wire the graph; `finish()` applies every parameter's control."""
        self._reset()

        self.hat_noise = Noise()
        self.hat_env = self.envelope(DROP, dur=DECAY, exp=self.decay_curve)
        self.hat_burst = self.hat_noise * self.hat_env

        # slow swell over 32 steps so the ticks don't sit at a fixed level
        self.hat_swell = Sine(freq=1 / (32 * context.tempo.sixteenth), mul=0.3, add=0.8)

        # high-pass to keep it thin and airy, out of the kick and bass range
        self.filtered = ButHP(self.hat_burst, mul=self.hat_swell)

        self.schedule_with(
            self.base_division, self.rate, context.clock, self.trigger.play
        )
        return self.finish(self.filtered)
