# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.drums.kick.kick style=round
#   style: round | punch | soft
"""Four-on-the-floor kick voices.

Each hit restarts a sine body at a zero crossing, so the impact starts at full
amplitude without a phase click. An exponential pitch drop gives the attack
its gesture, an exponential amplitude decay sets the body length, a short
noise burst clarifies the transient, and gentle saturation adds density.
"""

from typing import Any, ClassVar

from pyo.lib.effects import Disto
from pyo.lib.generators import Noise, Sine

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.patches.base import Patch
from pyoscillate.patches.drums.base import DrumVoice
from pyoscillate.patches.params import SliderSpec, rate_slider
from pyoscillate.tempo import Tempo

BASE_DIVISION = NoteDivision.QUARTER

PARAMETERS = (
    SliderSpec(
        "level",
        0.1,
        1.0,
        0.05,
        0.62,
        "Body",
        "Controls the fullness and weight of the kick's low end.",
    ),
    SliderSpec(
        "drive",
        0.0,
        0.8,
        0.05,
        0.12,
        "Grit",
        "Adds soft saturation warmth and edge; higher pushes the kick toward a grittier, more aggressive thump.",
    ),
    SliderSpec(
        "punch",
        0.0,
        2.0,
        0.05,
        1.0,
        "Punch",
        "Depth of the downward pitch drop at the start of each hit; more gives a sharper, more pronounced "
        "attack, too much starts to sound like a tom or zap, none leaves a pure low thud.",
    ),
    SliderSpec(
        "length",
        0.5,
        2.0,
        0.05,
        1.0,
        "Length",
        "Stretches or shortens the body; shorter is tight and dry and leaves room for the bass, longer is "
        "boomier and more 808-like but can mask the bassline.",
    ),
    SliderSpec(
        "click",
        0.0,
        2.0,
        0.05,
        1.0,
        "Click",
        "Level of the short noise transient on the attack; more adds snap and definition, less sounds "
        "rounder and softer.",
    ),
    rate_slider(
        BASE_DIVISION,
        "Halves or doubles the kick pattern speed for each step away from the four-on-the-floor default.",
    ),
)
# exponent of the amplitude and pitch decay curves - higher values give the
# fast-drop, long-tail shape of an analogue drum envelope; the body stays
# moderate so the kick keeps its weight
BODY_CURVE = 2.5
PITCH_CURVE = 6
CLICK_DURATION = 0.012
VOLUME_DEFAULT = 0.8


class Kick(DrumVoice):
    """Four-on-the-floor kick: pitch-enveloped sine body, noise-click
    transient, soft saturation. Style variants subclass this and override
    the profile attributes below with fixed data; the graph itself is
    identical across styles."""

    parameters = PARAMETERS
    volume_default = VOLUME_DEFAULT

    level: float
    drive: float
    punch: float
    length: float
    click: float
    rate: float

    # settled body pitch (Hz), pitch-drop depth (Hz above body), pitch-drop
    # time (s), body decay (s), transient level - overridden per style
    body_freq: ClassVar[float]
    sweep_depth: ClassVar[float]
    sweep_time: ClassVar[float]
    decay: ClassVar[float]
    click_level: ClassVar[float]

    def build(self, tempo: Tempo, clock: Clock, **values: Any) -> Patch:
        """Build a four-on-the-floor kick in this instance's style."""
        self.configure(**values)
        self._reset()

        pitch = self.envelope(
            [(0, 1), (8191, 0)],
            dur=self.sweep_time,
            mul=self.sweep_depth * self.punch,
            add=self.body_freq,
            exp=PITCH_CURVE,
        )
        body = Sine(freq=pitch)
        envelope = self.envelope(
            [(0, 1), (8191, 0)], dur=self.decay * self.length, mul=self.level, exp=BODY_CURVE
        )
        body_signal = body * envelope

        noise = Noise()
        click_env = self.envelope(
            [(0, 1), (8191, 0)],
            dur=CLICK_DURATION,
            mul=self.click_level * self.click,
            exp=PITCH_CURVE,
        )
        click_signal = noise * click_env

        source = body_signal + click_signal
        voice = Disto(source, drive=self.drive, slope=0.85)
        self.retain(body, body_signal, noise, click_signal, source)

        def strike() -> None:
            # restart the sine at phase zero so the full-level attack starts
            # on a zero crossing instead of wherever the oscillator last
            # stopped
            body.reset()
            self.trigger.play()

        self.schedule(BASE_DIVISION, self.rate, clock, strike)
        return self.finish(
            voice,
            {
                "level": lambda value: setattr(envelope, "mul", value),
                "drive": lambda value: setattr(voice, "drive", value),
                "punch": lambda value: setattr(pitch, "mul", self.sweep_depth * value),
                "length": lambda value: setattr(envelope, "dur", self.decay * value),
                "click": lambda value: setattr(click_env, "mul", self.click_level * value),
            },
        )


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
