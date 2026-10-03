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
from pyo.lib.generators import Sine
from pyo.lib.triggers import TrigEnv

from pyoscillate.clock import NoteDivision
from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.drums.base import RhythmDrum
from pyoscillate.patches.params import Param, rate_param
from pyoscillate.theory.phrase import Rhythms

# the tick's own default decay (s); read directly at construction (as well as
# from its own `@Param`) since there's no separate style constant behind it
DECAY = 0.12
# lower than the main hat (10300) so this reads as a darker, lower accent
CUTOFF_FREQ = 3000


class LowHat(RhythmDrum):
    """Darker noise tick, once per quarter note, as a rarer, dubbier accent."""

    title = "Low hat"
    summary = "Darker, rarer accent beneath the main hat."
    volume = Patch.volume.replace(default=0.2)
    phrase = RhythmDrum.phrase.replace(default=Rhythms.QUARTER_PULSE)
    base_division: ClassVar[NoteDivision] = NoteDivision.QUARTER
    # exponent of the decay curve - a sharp, strongly exponential drop keeps
    # the accent percussive even with a darker spectrum
    decay_curve: ClassVar[float] = 5
    # the top-end roll-off tracks the high-pass at this ratio, keeping the
    # voice a darker band of noise rather than a full-range hiss with the
    # lows removed
    top_ratio: ClassVar[float] = 3.0

    # the graph, assigned by build(); finish() retains every one of them
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
        sweep=True,
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
        self.apply_gains()

    @Param(
        0.03,
        0.6,
        0.01,
        DECAY,
        "Tail length",
        "Shapes the accent's decay; shorter feels tight and clipped, longer trails into a dubbier tock.",
        sweep=True,
    )
    def decay(self, value: float) -> None:
        self.hat_env.dur = value

    rate = rate_param(
        base_division,
        "Halves or doubles the accent pattern speed for each step away from its quarter-note grid.",
    )

    def apply_gains(self) -> None:
        self.hat_env.mul = self.level * self.accent

    def build(self, context: BuildContext) -> Patch:
        """Wire the graph; `finish()` applies every parameter's control."""
        self._reset()

        # same immediate, strongly exponential envelope shape as the main hat
        self.hat_env, self.hat_burst = self.noise_burst(dur=DECAY, exp=self.decay_curve)

        self.hat_swell = self.tempo_sine(
            context.tempo, lambda t: 32 * t.eighth, mul=0.3, add=0.8
        )

        # a gentler high-pass than the main hat keeps lower-mid body while
        # still clearing the kick and bass; the linked low-pass removes the
        # airy top
        self.low_edge = Sig(self.cutoff_freq)
        self.high_edge = self.low_edge * self.top_ratio
        self.body = ButHP(self.hat_burst, freq=self.low_edge)
        self.filtered = ButLP(self.body, freq=self.high_edge, mul=self.hat_swell)

        self.schedule_pattern(context)
        return self.finish(self.filtered)
