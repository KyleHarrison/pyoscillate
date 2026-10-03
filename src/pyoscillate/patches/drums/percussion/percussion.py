# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.drums.percussion.percussion
#   style: rim | conga
"""Rim and conga-like accent percussion voices.

Both styles share one construction: a sine body that bends slightly down in
pitch as it strikes, plus a short noise transient rung through a band-pass
tuned relative to the body. The rim keeps the body very short and the
transient bright and woody; the conga uses a lower, longer body with only a
soft touch of transient, a warmer answer to the kick.
"""

from typing import ClassVar

from pyo import PyoObject
from pyo.lib._core import Sig
from pyo.lib.filters import Biquad
from pyo.lib.triggers import TrigEnv

from pyoscillate.clock import NoteDivision
from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.drums.base import RhythmDrum, semitone_ratio
from pyoscillate.patches.params import Param, rate_param
from pyoscillate.theory import notes
from pyoscillate.theory.intervals import Rhythm


class Percussion(RhythmDrum):
    """Rim-click or conga-like accent from a bent sine body and a
    band-passed noise transient. Style variants share this graph and
    override the profile attributes below."""

    volume = Patch.volume.replace(default=0.28)
    base_division: ClassVar[NoteDivision] = NoteDivision.SIXTEENTH
    decay_curve: ClassVar[float] = 3
    bend_curve: ClassVar[float] = 6
    click_duration: ClassVar[float] = 0.008

    # body pitch (Hz), pitch bend (fraction above body
    # at the strike), bend time (s), body decay (s), transient level,
    # transient pitch (ratio to body), transient resonance - overridden per
    # style
    base_freq: ClassVar[float]
    bend_depth: ClassVar[float]
    bend_time: ClassVar[float]
    decay: ClassVar[float]
    click_level: ClassVar[float]
    click_ratio: ClassVar[float]
    click_q: ClassVar[float]

    # the graph, assigned by build(); finish() retains every one of them
    tuning: Sig
    body_freq: PyoObject
    click_env: TrigEnv
    click_burst: PyoObject
    click_freq: PyoObject
    click_signal: Biquad
    source: PyoObject

    @Param(
        0.02,
        0.6,
        0.01,
        0.18,
        "Presence",
        "Sets how loud and upfront the percussion accent sits in the mix.",
    )
    def level(self, value: float) -> None:
        self.body_env.mul = value
        self.click_env.mul = self.click_level * self.click * value

    @Param(
        -12,
        12,
        1,
        0,
        "Pitch",
        "Retunes the accent in semitones; lower is deeper and woodier, higher is thinner and sharper.",
    )
    def tune(self, value: float) -> None:
        self.tuning.value = semitone_ratio(value)

    @Param(
        0.5,
        2.0,
        0.05,
        1.0,
        "Length",
        "Shortens the accent toward a dry, clipped tick or lets it ring out into a rounder, more resonant tone.",
        sweep=True,
    )
    def length(self, value: float) -> None:
        self.body_env.dur = self.decay * value

    @Param(
        0.0,
        2.0,
        0.05,
        1.0,
        "Attack",
        "Level of the woody transient on each hit; more gives a sharper, clickier strike, less leaves a "
        "softer, purely tonal hit.",
        sweep=True,
    )
    def click(self, value: float) -> None:
        self.click_env.mul = self.click_level * value * self.level

    rate = rate_param(
        base_division,
        "Halves or doubles the accent pattern speed for each step away from its 16th-note grid.",
    )

    def build(self, context: BuildContext) -> Patch:
        self._reset()
        self.tuning = Sig(semitone_ratio(self.tune))
        self.body_freq = self.tuning * self.base_freq

        self.pitched_body(
            self.body_freq,
            bend_depth=self.bend_depth,
            bend_time=self.bend_time,
            bend_curve=self.bend_curve,
            decay=self.decay,
            decay_curve=self.decay_curve,
        )

        self.click_env, self.click_burst = self.noise_burst(
            dur=self.click_duration, exp=self.bend_curve
        )
        self.click_freq = self.body_freq * self.click_ratio
        self.click_signal = Biquad(
            self.click_burst, freq=self.click_freq, q=self.click_q, type=2
        )

        self.source = self.body_signal + self.click_signal

        self.schedule_pattern(context)
        return self.finish(self.source)


class PercussionRim(Percussion):
    """Tight, woody rim-click accent."""

    rhythm = Percussion.rhythm.replace(default=Rhythm.RIM_OFFBEATS.index)
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

    rhythm = Percussion.rhythm.replace(default=Rhythm.CONGA_SYNCOPATED.index)
    base_freq, bend_depth, bend_time, decay, click_level, click_ratio, click_q = (
        notes.A3,
        0.2,
        0.03,
        0.28,
        0.2,
        4.0,
        3.0,
    )
