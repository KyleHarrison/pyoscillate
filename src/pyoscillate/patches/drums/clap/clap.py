# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.drums.clap.clap
"""Multi-burst noise clap voice.

A clap is several nearly simultaneous noise bursts rather than one hit: a few
short, sawtooth-like bursts are followed by a longer exponential tail, and the
whole envelope shapes white noise band-passed into the papery clap region.
"""

import math

from pyo.lib.filters import Biquad
from pyo.lib.generators import Noise
from pyo.lib.tables import LinTable
from pyo.lib.triggers import TrigEnv

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.patches.base import BuiltPatch
from pyoscillate.patches.drums.base import DrumVoice
from pyoscillate.patches.params import SliderSpec, rate_slider
from pyoscillate.tempo import Tempo

BASE_DIVISION = NoteDivision.SIXTEENTH

PARAMETERS = (
    SliderSpec(
        "level",
        0.02,
        0.6,
        0.01,
        0.18,
        "Presence",
        "Sets how loud and upfront the clap accent sits in the mix.",
    ),
    SliderSpec(
        "tone",
        400,
        4000,
        20,
        1100,
        "Brightness",
        "Moves the clap from fuller and softer to thinner and sharper.",
    ),
    SliderSpec(
        "spread",
        0.003,
        0.02,
        0.001,
        0.009,
        "Width",
        "Spacing between the hands arriving; wider sounds fuzzier and more human, tighter moves toward a "
        "single direct noise hit.",
    ),
    SliderSpec(
        "decay",
        0.04,
        0.5,
        0.01,
        0.14,
        "Tail",
        "Length of the noisy tail after the burst; short is dry and crisp, long reads like a small room "
        "around the clap.",
    ),
    rate_slider(
        BASE_DIVISION,
        "Steps the clap pattern to a slower or faster bar division - -1 "
        "drops to an 8th note (half speed), 0 is the default 16th note, "
        "+1 rises to a 32nd note (double speed).",
    ),
)
PATTERN = {4, 12}
# short bursts before the tail; the tail's onset acts as the final hand
BURSTS = 3
# level each burst decays to before the next hand arrives
BURST_FLOOR = 0.2
TAIL_POINTS = 24
TAIL_CURVE = 5.0
TABLE_SIZE = 8192
# moderate resonance gives a focused snap without ringing
RESONANCE = 1.4
# band-passing leaves much less energy than broadband noise; restores the
# clap to roughly the same loudness as the rest of the kit at REFERENCE_TONE
MAKEUP_GAIN = 5.0
REFERENCE_TONE = 1100
VOLUME_DEFAULT = 0.28


def _envelope(spread: float, decay: float) -> tuple[list[tuple[int, float]], float]:
    """Envelope table points and total duration for one multi-burst clap."""
    total = BURSTS * spread + decay
    scale = (TABLE_SIZE - 1) / total
    points: list[tuple[int, float]] = [(0, 0.0)]
    for burst in range(BURSTS + 1):
        start = round(burst * spread * scale)
        if burst:
            points.append((start, BURST_FLOOR))
        points.append((start + 1, 1.0))
    tail_start = points[-1][0]
    for step in range(1, TAIL_POINTS + 1):
        fraction = step / TAIL_POINTS
        index = tail_start + round(fraction * (TABLE_SIZE - 1 - tail_start))
        value = math.exp(-TAIL_CURVE * fraction) if step < TAIL_POINTS else 0.0
        points.append((index, value))
    return points, total


def _makeup(tone: float) -> float:
    """Gain that keeps loudness steady as Brightness moves.

    A constant-Q band-pass lets through bandwidth proportional to its centre,
    so noise power rises with `tone`; scaling by the square root cancels that.
    """
    return MAKEUP_GAIN * math.sqrt(REFERENCE_TONE / tone)


class Clap(DrumVoice):
    """Multi-burst, band-passed noise clap on beats two and four.

    Doesn't use `self.envelope()`: the burst/tail shape needs a `LinTable`
    reshaped live (`.replace(...)`), not a fixed `ExpTable`.
    """

    parameters = PARAMETERS
    volume_default = VOLUME_DEFAULT

    def build(
        self,
        tempo: Tempo,
        clock: Clock,
        level: float = 0.18,
        tone: float = 1100,
        spread: float = 0.009,
        decay: float = 0.14,
        rate: float = 0,
    ) -> BuiltPatch:
        self._reset()
        shape = {"spread": spread, "decay": decay}
        points, duration = _envelope(spread, decay)
        envelope_table = LinTable(points, size=TABLE_SIZE)
        envelope = TrigEnv(self.trigger, envelope_table, dur=duration, mul=level)
        noise = Noise()
        source = noise * envelope
        voice = Biquad(source, freq=tone, q=RESONANCE, type=2, mul=_makeup(tone))
        self.retain(envelope_table, envelope, noise, source)

        step = self.step_pattern(16, PATTERN)

        def next_step() -> None:
            if step()[1] is not None:
                self.trigger.play()

        def set_tone(value: float) -> None:
            voice.freq = value
            voice.mul = _makeup(value)

        def set_shape(name: str, value: float) -> None:
            # the burst structure lives in the table, so reshape it in place
            # rather than rebuilding the graph
            shape[name] = value
            new_points, new_duration = _envelope(shape["spread"], shape["decay"])
            envelope_table.replace(new_points)
            envelope.dur = new_duration

        self.schedule(BASE_DIVISION, rate, clock, next_step)
        return self.finish(
            voice,
            {
                "level": lambda value: setattr(envelope, "mul", value),
                "tone": set_tone,
                "spread": lambda value: set_shape("spread", value),
                "decay": lambda value: set_shape("decay", value),
            },
        )
