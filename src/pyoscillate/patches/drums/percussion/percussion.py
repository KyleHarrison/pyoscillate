# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.drums.percussion.percussion style=rim
#   style: rim | conga
"""Rim and conga-like accent percussion voices.

Both styles share one construction: a sine body that bends slightly down in
pitch as it strikes, plus a short noise transient rung through a band-pass
tuned relative to the body. The rim keeps the body very short and the
transient bright and woody; the conga uses a lower, longer body with only a
soft touch of transient, a warmer answer to the kick.
"""

from typing import Any, ClassVar

from pyo.lib._core import Sig
from pyo.lib.filters import Biquad
from pyo.lib.generators import Noise, Sine

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.patches.base import Patch
from pyoscillate.patches.drums.base import DrumVoice, semitone_ratio
from pyoscillate.patches.params import SliderSpec
from pyoscillate.patches.utility.notes import notes
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
        "Sets how loud and upfront the percussion accent sits in the mix.",
    ),
    SliderSpec(
        "tune",
        -12,
        12,
        1,
        0,
        "Pitch",
        "Retunes the accent in semitones; lower is deeper and woodier, higher is thinner and sharper.",
    ),
    SliderSpec(
        "length",
        0.5,
        2.0,
        0.05,
        1.0,
        "Length",
        "Shortens the accent toward a dry, clipped tick or lets it ring out into a rounder, more resonant tone.",
    ),
    SliderSpec(
        "click",
        0.0,
        2.0,
        0.05,
        1.0,
        "Attack",
        "Level of the woody transient on each hit; more gives a sharper, clickier strike, less leaves a "
        "softer, purely tonal hit.",
    ),
    SliderSpec(
        "rate",
        Clock.rate_limits(BASE_DIVISION)[0],
        Clock.rate_limits(BASE_DIVISION)[1],
        1,
        0,
        "Rate",
        "Halves or doubles the accent pattern speed for each step away from its 16th-note grid.",
    ),
)
DECAY_CURVE = 3
BEND_CURVE = 6
CLICK_DURATION = 0.008
VOLUME_DEFAULT = 0.28


class Percussion(DrumVoice):
    """Rim-click or conga-like accent from a bent sine body and a
    band-passed noise transient. Style variants share this graph and
    override the profile attributes below."""

    parameters = PARAMETERS
    volume_default = VOLUME_DEFAULT

    level: float
    tune: float
    length: float
    click: float
    rate: float

    # step-in-16 pattern; body pitch (Hz), pitch bend (fraction above body
    # at the strike), bend time (s), body decay (s), transient level,
    # transient pitch (ratio to body), transient resonance - overridden per
    # style
    pattern: ClassVar[set[int]]
    base_freq: ClassVar[float]
    bend_depth: ClassVar[float]
    bend_time: ClassVar[float]
    decay: ClassVar[float]
    click_level: ClassVar[float]
    click_ratio: ClassVar[float]
    click_q: ClassVar[float]

    def build(self, tempo: Tempo, clock: Clock, **values: Any) -> Patch:
        self.configure(**values)
        self._reset()
        tuning = Sig(semitone_ratio(self.tune))
        body_freq = tuning * self.base_freq

        bend = self.envelope(
            [(0, 1), (8191, 0)], dur=self.bend_time, mul=self.bend_depth, add=1, exp=BEND_CURVE
        )
        pitch = body_freq * bend
        body = Sine(freq=pitch)
        envelope = self.envelope(
            [(0, 1), (8191, 0)], dur=self.decay * self.length, mul=self.level, exp=DECAY_CURVE
        )
        body_signal = body * envelope

        noise = Noise()
        click_env = self.envelope(
            [(0, 1), (8191, 0)],
            dur=CLICK_DURATION,
            mul=self.click_level * self.click * self.level,
            exp=BEND_CURVE,
        )
        click_burst = noise * click_env
        click_freq = body_freq * self.click_ratio
        click_signal = Biquad(click_burst, freq=click_freq, q=self.click_q, type=2)

        voice = body_signal + click_signal
        self.retain(tuning, body_freq, pitch, body, body_signal, noise, click_burst, click_freq, click_signal)
        state = {"level": self.level, "click": self.click}

        step = self.step_pattern(16, self.pattern)

        def next_step() -> None:
            _, hit = step()
            if hit is not None:
                # restart the body on a zero crossing so the immediate
                # attack doesn't click wherever the oscillator last stopped
                body.reset()
                self.trigger.play()

        def set_level(value: float) -> None:
            state["level"] = value
            envelope.mul = value
            click_env.mul = self.click_level * state["click"] * value

        def set_click(value: float) -> None:
            state["click"] = value
            click_env.mul = self.click_level * value * state["level"]

        self.schedule(BASE_DIVISION, self.rate, clock, next_step)
        return self.finish(
            voice,
            {
                "level": set_level,
                "tune": lambda value: setattr(tuning, "value", semitone_ratio(value)),
                "length": lambda value: setattr(envelope, "dur", self.decay * value),
                "click": set_click,
            },
        )


class PercussionRim(Percussion):
    """Tight, woody rim-click accent."""

    pattern: ClassVar[set[int]] = {3, 7, 11, 15}
    base_freq, bend_depth, bend_time, decay, click_level, click_ratio, click_q = (
        1100.0,
        0.12,
        0.008,
        0.07,
        0.9,
        1.6,
        6.0,
    )


class PercussionConga(Percussion):
    """Warm, resonant conga-like rhythmic color."""

    pattern: ClassVar[set[int]] = {3, 6, 9, 11, 14}
    base_freq, bend_depth, bend_time, decay, click_level, click_ratio, click_q = (
        notes.A3,
        0.2,
        0.03,
        0.28,
        0.2,
        4.0,
        3.0,
    )
