# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.drums.clap.clap
"""Multi-burst noise clap voice.

A clap is several nearly simultaneous noise bursts rather than one hit: a few
short, sawtooth-like bursts are followed by a longer exponential tail, and the
whole envelope shapes white noise band-passed into the papery clap region.
"""

import math
from typing import ClassVar

from pyo import PyoObject
from pyo.lib.filters import Biquad
from pyo.lib.generators import Noise
from pyo.lib.tables import LinTable
from pyo.lib.triggers import TrigEnv

from pyoscillate.clock import NoteDivision
from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.drums.base import DrumVoice
from pyoscillate.patches.params import Param, rate_param


class Clap(DrumVoice):
    """Multi-burst, band-passed noise clap on beats two and four.

    Doesn't use `self.envelope()`: the burst/tail shape needs a `LinTable`
    reshaped live (`.replace(...)`), not a fixed `ExpTable`.
    """

    summary = "Sharp, bright clap accent."
    volume = Patch.volume.replace(default=0.28)
    base_division: ClassVar[NoteDivision] = NoteDivision.SIXTEENTH
    # beats two and four of a 16-step bar - the backbeat this clap accents
    pattern: ClassVar[set[int]] = {4, 12}
    pattern_cycle: ClassVar[int] = 16
    # short bursts before the tail; the tail's onset acts as the final hand
    bursts: ClassVar[int] = 3
    # level each burst decays to before the next hand arrives
    burst_floor: ClassVar[float] = 0.2
    tail_points: ClassVar[int] = 24
    tail_curve: ClassVar[float] = 5.0
    # pyo's default table length; break-point indices are in table samples
    table_size: ClassVar[int] = 8192
    # moderate resonance gives a focused snap without ringing
    resonance: ClassVar[float] = 1.4
    # band-passing leaves much less energy than broadband noise; restores the
    # clap to roughly the same loudness as the rest of the kit at reference_tone
    makeup_gain: ClassVar[float] = 5.0
    reference_tone: ClassVar[float] = 1100

    # the graph, assigned by build(); finish() retains every one of them
    envelope_table: LinTable
    burst_env: TrigEnv
    noise: Noise
    source: PyoObject
    tone_filter: Biquad

    @Param(
        0.02,
        0.3,
        0.01,
        0.18,
        "Presence",
        "Sets how loud and upfront the clap accent sits in the mix.",
    )
    def level(self, value: float) -> None:
        self.burst_env.mul = value

    @Param(
        400,
        4000,
        20,
        1100,
        "Brightness",
        "Moves the clap from fuller and softer to thinner and sharper.",
        sweep=True,
    )
    def tone(self, value: float) -> None:
        self.tone_filter.freq = value
        self.tone_filter.mul = self._makeup(value)

    @Param(
        0.003,
        0.02,
        0.001,
        0.009,
        "Width",
        "Spacing between the hands arriving; wider sounds fuzzier and more human, tighter moves toward a "
        "single direct noise hit.",
        sweep=True,
    )
    def spread(self, value: float) -> None:
        self._reshape()

    @Param(
        0.04,
        0.5,
        0.01,
        0.14,
        "Tail",
        "Length of the noisy tail after the burst; short is dry and crisp, long reads like a small room "
        "around the clap.",
        sweep=True,
    )
    def decay(self, value: float) -> None:
        self._reshape()

    rate = rate_param(
        base_division,
        "Steps the clap pattern to a slower or faster bar division - -1 "
        "drops to an 8th note (half speed), 0 is the default 16th note, "
        "+1 rises to a 32nd note (double speed).",
    )

    def _envelope_points(
        self, spread: float, decay: float
    ) -> tuple[list[tuple[int, float]], float]:
        """Envelope table points and total duration for one multi-burst clap."""
        total = self.bursts * spread + decay
        scale = (self.table_size - 1) / total
        points: list[tuple[int, float]] = [(0, 0.0)]
        for burst in range(self.bursts + 1):
            start = round(burst * spread * scale)
            if burst:
                points.append((start, self.burst_floor))
            points.append((start + 1, 1.0))
        tail_start = points[-1][0]
        for step in range(1, self.tail_points + 1):
            fraction = step / self.tail_points
            index = tail_start + round(fraction * (self.table_size - 1 - tail_start))
            value = (
                math.exp(-self.tail_curve * fraction)
                if step < self.tail_points
                else 0.0
            )
            points.append((index, value))
        return points, total

    def _makeup(self, tone: float) -> float:
        """Gain that keeps loudness steady as Brightness moves.

        A constant-Q band-pass lets through bandwidth proportional to its centre,
        so noise power rises with `tone`; scaling by the square root cancels that.
        """
        return self.makeup_gain * math.sqrt(self.reference_tone / tone)

    def _reshape(self) -> None:
        """Reshape the burst/tail envelope in place from the current Width
        and Tail values - the burst structure lives in the table, so this
        rewrites it rather than rebuilding the graph."""
        points, duration = self._envelope_points(self.spread, self.decay)
        self.envelope_table.replace(points)
        self.burst_env.dur = duration

    def build(self, context: BuildContext) -> Patch:
        self._reset()

        points, duration = self._envelope_points(self.spread, self.decay)
        self.envelope_table = LinTable(points, size=self.table_size)
        self.burst_env = TrigEnv(
            self.trigger, self.envelope_table, dur=duration, mul=self.level
        )
        self.noise = Noise()
        self.source = self.noise * self.burst_env
        self.tone_filter = Biquad(
            self.source,
            freq=self.tone,
            q=self.resonance,
            type=2,
            mul=self._makeup(self.tone),
        )

        self.schedule_pattern(context)
        return self.finish(self.tone_filter)
