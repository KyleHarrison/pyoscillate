"""Drums-archetype base: the shape every gated drum voice shares.

Every gated drum voice (kick, snare, clap, hat, ...) follows the same shape
`GatedVoice` (`pyoscillate.patches.common`) factors out: one `Trig()` fires
per hit, one or more `TrigEnv`s read a break-point table off it, and a
`Clock` `Division` schedules the hit with a live `rate` control. `DrumVoice`
adds what the drums themselves repeat on top of that: the per-step accent
pattern and its `next_step`, restarting the oscillators' phase on a hit, and
the pitched body (a sine with a downward bend) that most of the kit is built
around, so a concrete drum only supplies what makes it that drum.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import ClassVar

from pyo import PyoObject
from pyo.lib.generators import Noise, Sine
from pyo.lib.triggers import TrigEnv

from pyoscillate.clock import NoteDivision
from pyoscillate.patches.common import GatedVoice, Rhythmic, Step
from pyoscillate.theory.notes import semitone_ratio

__all__ = ["DROP", "DrumVoice", "RhythmDrum", "semitone_ratio"]

# full-to-zero break-points shared by every drum envelope; `exp` sets the curve
DROP = [(0, 1), (8191, 0)]


class DrumVoice(GatedVoice):
    """Base for a gated drums-archetype voice. See `GatedVoice` for the
    shared `self.envelope(...)`/`self.schedule(...)`/`self.finish(...)`
    contract every concrete voice builds on.

    A voice that plays a step pattern selects it with a dropdown `Param`
    (`RhythmDrum` for a `Rhythm`) and calls `self.schedule_pattern(context)`
    from `build()`. It overrides `apply_gains()` when its level depends on the
    current step's `accent`, and `strike()` for anything extra a hit does.
    `base_division` only sets the range of the rate slider: the grid a hit
    lands on is the chosen pattern's own.
    """

    base_division: ClassVar[NoteDivision]

    # per-hit accent from the pattern's velocity, not a parameter: kept on self
    # so a live level change doesn't lose the current step's accent
    accent: float
    # oscillators restarted at phase zero on every hit, so the attack starts
    # on a zero crossing instead of wherever they last stopped
    phased: list[Sine]
    # the step pattern's callable, assigned by `schedule_pattern()`
    _step: Callable[[], Step]

    # the pitched body, assigned by `pitched_body()`
    bend: TrigEnv
    pitch: PyoObject
    body: Sine
    body_env: TrigEnv
    body_signal: PyoObject

    # the noise source shared by every `noise_burst()`, assigned by it
    noise: Noise

    def _reset(self) -> None:
        super()._reset()
        self.accent = 1.0
        self.phased = []

    def pitched_body(
        self,
        freq: PyoObject | float,
        *,
        bend_depth: float,
        bend_time: float,
        bend_curve: float,
        decay: float,
        decay_curve: float,
    ) -> PyoObject:
        """A sine body whose pitch starts `bend_depth` (a fraction of `freq`)
        above it and falls over `bend_time`, under a `decay`-long amplitude
        envelope. Every node lands on `self`; the oscillator joins `phased`.
        Returns the enveloped body."""
        self.bend = self.envelope(
            DROP, dur=bend_time, mul=bend_depth, add=1, exp=bend_curve
        )
        self.pitch = freq * self.bend
        self.body = Sine(freq=self.pitch)
        self.phased.append(self.body)
        self.body_env = self.envelope(DROP, dur=decay, exp=decay_curve)
        self.body_signal = self.body * self.body_env
        return self.body_signal

    def noise_burst(self, *, dur: float, exp: float) -> tuple[TrigEnv, PyoObject]:
        """A `dur`-long decaying burst of white noise. `self.noise` is the
        source; returns the envelope (for its live `mul`/`dur`) and the
        enveloped burst, which the caller assigns to its own names."""
        self.noise = Noise()
        env = self.envelope(DROP, dur=dur, exp=exp)
        return env, self.noise * env

    def apply_gains(self) -> None:
        """Recombine the current level controls with this hit's `accent`.
        A no-op unless a voice's level depends on its step accent."""

    def strike(self) -> None:
        """Play one hit: restart the `phased` oscillators, then fire."""
        for oscillator in self.phased:
            oscillator.reset()
        self.trigger.play()


class RhythmDrum(Rhythmic, DrumVoice):
    """A drum that plays a `Rhythm` chosen by its `rhythm` dropdown: each hit
    carries its step's velocity as `accent`. A voice names its starting
    rhythm with `rhythm = Voice.rhythm.replace(default=Rhythm.X.index)` and
    gets `next_step` for free."""

    def next_step(self) -> None:
        step = self._step()
        if not step.hit:
            return
        self.accent = float(step.value)
        self.apply_gains()
        self.strike()
