# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.drums.low_hat
"""Darker noise tick, once per quarter note, as a rarer, dubbier accent.

Like the main hat's tick, a noise burst is shaped by a fast exponential decay
and slowly swelled in level, but band-limited lower - a gentler high-pass
paired with a linked low-pass - so it reads as a darker, closer thud rather
than an airy hiss.
"""

from typing import ClassVar

from pyo import PyoObject
from pyo.lib._core import Sig
from pyo.lib.filters import ButHP, ButLP
from pyo.lib.generators import Noise, Sine
from pyo.lib.triggers import TrigEnv

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.patches.base import Patch
from pyoscillate.patches.drums.base import DrumVoice
from pyoscillate.patches.params import Param, rate_param
from pyoscillate.tempo import Tempo

# full-to-zero break-points shared by the tick's envelope
DROP = [(0, 1), (8191, 0)]
# the tick's own default decay (s); read directly at construction (as well as
# from its own `@Param`) since there's no separate style constant behind it
DECAY = 0.12
# lower than the main hat (10300) so this reads as a darker, lower accent
CUTOFF_FREQ = 3000


class LowHat(DrumVoice):
    """Darker noise tick, once per quarter note, as a rarer, dubbier accent."""

    title = "Low hat"
    summary = "Darker, rarer accent beneath the main hat."
    volume_default = 0.2
    base_division: ClassVar[NoteDivision] = NoteDivision.QUARTER
    # exponent of the decay curve - a sharp, strongly exponential drop keeps
    # the accent percussive even with a darker spectrum
    decay_curve: ClassVar[float] = 5
    # the top-end roll-off tracks the high-pass at this ratio, keeping the
    # voice a darker band of noise rather than a full-range hiss with the
    # lows removed
    top_ratio: ClassVar[float] = 3.0

    # the graph, assigned by build(); finish() retains every one of them
    hat_noise: Noise
    hat_env: TrigEnv
    hat_burst: PyoObject
    hat_swell: Sine
    low_edge: Sig
    high_edge: PyoObject
    body: ButHP
    filtered: ButLP

    @Param(
        1000,
        6000,
        100,
        CUTOFF_FREQ,
        "Darkness",
        "Sets how dark and low this accent sits against the main hat; lower is closer to a thud, higher "
        "brightens it toward the main hat's character.",
    )
    def cutoff_freq(self, value: float) -> None:
        self.low_edge.value = value

    @Param(
        0,
        1,
        0.05,
        0.55,
        "Presence",
        "Controls how prominent this accent is against the main hat.",
    )
    def level(self, value: float) -> None:
        self.hat_env.mul = value

    @Param(
        0.03,
        0.6,
        0.01,
        DECAY,
        "Tail length",
        "Shapes the accent's decay; shorter feels tight and clipped, longer trails into a dubbier tock.",
    )
    def decay(self, value: float) -> None:
        self.hat_env.dur = value

    rate = rate_param(
        base_division,
        "Halves or doubles the accent pattern speed for each step away from its quarter-note grid.",
    )

    def build(self, tempo: Tempo, clock: Clock) -> Patch:
        """Wire the graph; `finish()` applies every parameter's control."""
        self._reset()

        self.hat_noise = Noise()
        # same immediate, strongly exponential envelope shape as the main hat
        self.hat_env = self.envelope(DROP, dur=DECAY, exp=self.decay_curve)
        self.hat_burst = self.hat_noise * self.hat_env

        self.hat_swell = Sine(freq=1 / (32 * tempo.eighth), mul=0.3, add=0.8)

        # a gentler high-pass than the main hat keeps lower-mid body while
        # still clearing the kick and bass; the linked low-pass removes the
        # airy top
        self.low_edge = Sig(self.cutoff_freq)
        self.high_edge = self.low_edge * self.top_ratio
        self.body = ButHP(self.hat_burst, freq=self.low_edge)
        self.filtered = ButLP(self.body, freq=self.high_edge, mul=self.hat_swell)

        self.schedule(self.base_division, self.rate, clock, self.trigger.play)
        return self.finish(self.filtered)
