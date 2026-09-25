# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.drums.kick.kick style=round
#   style: round | punch | soft
"""Four-on-the-floor kick voices.

Each hit restarts a sine body at a zero crossing, so the impact starts at full
amplitude without a phase click. An exponential pitch drop gives the attack
its gesture, an exponential amplitude decay sets the body length, a short
noise burst clarifies the transient, and gentle saturation adds density.
"""

from typing import ClassVar

from pyo import PyoObject
from pyo.lib.effects import Disto
from pyo.lib.generators import Noise, Sine
from pyo.lib.triggers import TrigEnv

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.patches.base import Patch
from pyoscillate.patches.drums.base import DrumVoice
from pyoscillate.patches.params import Param, rate_param
from pyoscillate.tempo import Tempo

# full-to-zero break-points shared by every envelope; `exp` sets the curve
DROP = [(0, 1), (8191, 0)]


class Kick(DrumVoice):
    """Four-on-the-floor kick: pitch-enveloped sine body, noise-click
    transient, soft saturation. Style variants subclass this and override
    the profile attributes below with fixed data; the graph itself is
    identical across styles."""

    volume_default = 0.8
    base_division: ClassVar[NoteDivision] = NoteDivision.QUARTER
    # exponent of the amplitude and pitch decay curves - higher values give the
    # fast-drop, long-tail shape of an analogue drum envelope; the body stays
    # moderate so the kick keeps its weight
    body_curve: ClassVar[float] = 2.5
    pitch_curve: ClassVar[float] = 6
    click_duration: ClassVar[float] = 0.012

    # settled body pitch (Hz), pitch-drop depth (Hz above body), pitch-drop
    # time (s), body decay (s), transient level - overridden per style
    body_freq: ClassVar[float]
    sweep_depth: ClassVar[float]
    sweep_time: ClassVar[float]
    decay: ClassVar[float]
    click_level: ClassVar[float]

    # the graph, assigned by build(); finish() retains every one of them
    pitch_env: TrigEnv
    body: Sine
    body_env: TrigEnv
    body_signal: PyoObject
    noise: Noise
    click_env: TrigEnv
    click_signal: PyoObject
    source: PyoObject
    shaper: Disto

    @Param(0.1, 1.0, 0.05, 0.62, "Body", "Controls the fullness and weight of the kick's low end.")
    def level(self, value: float) -> None:
        self.body_env.mul = value

    @Param(
        0.0,
        0.8,
        0.05,
        0.12,
        "Grit",
        "Adds soft saturation warmth and edge; higher pushes the kick toward a grittier, more aggressive thump.",
    )
    def drive(self, value: float) -> None:
        self.shaper.drive = value

    @Param(
        0.0,
        2.0,
        0.05,
        1.0,
        "Punch",
        "Depth of the downward pitch drop at the start of each hit; more gives a sharper, more pronounced "
        "attack, too much starts to sound like a tom or zap, none leaves a pure low thud.",
    )
    def punch(self, value: float) -> None:
        self.pitch_env.mul = self.sweep_depth * value

    @Param(
        0.5,
        2.0,
        0.05,
        1.0,
        "Length",
        "Stretches or shortens the body; shorter is tight and dry and leaves room for the bass, longer is "
        "boomier and more 808-like but can mask the bassline.",
    )
    def length(self, value: float) -> None:
        self.body_env.dur = self.decay * value

    @Param(
        0.0,
        2.0,
        0.05,
        1.0,
        "Click",
        "Level of the short noise transient on the attack; more adds snap and definition, less sounds "
        "rounder and softer.",
    )
    def click(self, value: float) -> None:
        self.click_env.mul = self.click_level * value

    rate = rate_param(
        base_division,
        "Halves or doubles the kick pattern speed for each step away from the four-on-the-floor default.",
    )

    def build(self, tempo: Tempo, clock: Clock) -> Patch:
        """Wire the graph; `finish()` applies every parameter's control."""
        self._reset()

        self.pitch_env = self.envelope(
            DROP, dur=self.sweep_time, add=self.body_freq, exp=self.pitch_curve
        )
        self.body = Sine(freq=self.pitch_env)
        self.body_env = self.envelope(DROP, dur=self.decay, exp=self.body_curve)
        self.body_signal = self.body * self.body_env

        self.noise = Noise()
        self.click_env = self.envelope(DROP, dur=self.click_duration, exp=self.pitch_curve)
        self.click_signal = self.noise * self.click_env

        self.source = self.body_signal + self.click_signal
        self.shaper = Disto(self.source, slope=0.85)

        def strike() -> None:
            # restart the sine at phase zero so the full-level attack starts
            # on a zero crossing instead of wherever the oscillator last
            # stopped
            self.body.reset()
            self.trigger.play()

        self.schedule(self.base_division, self.rate, clock, strike)
        return self.finish(self.shaper)


class KickRound(Kick):
    """Deep, rounded low-end thump."""

    summary = "Deep, rounded low-end thump anchoring the groove."
    body_freq, sweep_depth, sweep_time, decay, click_level = 50.0, 80.0, 0.05, 0.27, 0.12


class KickPunch(Kick):
    """Tighter, punchier kick with more transient snap."""

    body_freq, sweep_depth, sweep_time, decay, click_level = 54.0, 140.0, 0.035, 0.2, 0.28


class KickSoft(Kick):
    """Soft, cushioned kick that sits back in the mix."""

    body_freq, sweep_depth, sweep_time, decay, click_level = 46.0, 50.0, 0.07, 0.37, 0.05
