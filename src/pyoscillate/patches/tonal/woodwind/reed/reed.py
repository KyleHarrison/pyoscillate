# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.woodwind.reed.single
"""Reed winds: a reed chopping the breath into pulses, a bore shaping them.

A reed is a valve: the player's breath leaves it as a stream of pressure
pulses, and the pipe decides which harmonics of those pulses survive. A
cylindrical bore with a reed at one end is a closed pipe, so it keeps only the
odd harmonics (the clarinet's hollow, square-wave sound); a conical bore keeps
the whole series (the oboe, bassoon and saxophone's fuller, sawtooth-like
sound). `ReedWind` is that source for the whole family: `Bore` slides between
the two by fading the even harmonics in, `Reed edge` sets how quickly the
harmonics fall away (a soft, rounded reed to a buzzing one), and `Nasal` adds
the double reed's fixed resonance. The partials are normalised, so none of
the three changes the loudness. Everything else a wind has (the pipe's
low-pass that opens as a note swells and rises with the pitch, tonguing, the
breath pulse, the scoop) is `Wind`'s (see `wind.py`).
"""

from __future__ import annotations

from typing import ClassVar

from pyo import PyoObject
from pyo.lib._core import Mix
from pyo.lib.controls import SigTo
from pyo.lib.filters import Reson
from pyo.lib.generators import Sine

from pyoscillate.patches.params import Param
from pyoscillate.patches.tonal.woodwind.wind import Wind


class ReedWind(Wind):
    """A reed-driven pipe: the harmonic series of a reed's pulse, odd only in
    a cylinder and whole in a cone. A style sets the register, the bore, the
    reed and how the note is articulated."""

    # harmonics in the source; a reed's pulse is rich, but the pipe's low-pass
    # has closed over everything near the top of this range
    partials: ClassVar[int] = 16
    # the slope of the harmonics' fall, 1/n to the power of this: `Reed edge`
    # moves it from `soft_slope` (rounded, nearly sine) to `buzz_slope`
    # (buzzing); 1 is the sawtooth's (and the square's, odd only)
    soft_slope: ClassVar[float] = 2.2
    buzz_slope: ClassVar[float] = 0.6
    # where the bell and the reed's double blades ring (Hz), how sharply, and
    # the level of that ring against the tone at full Nasal
    nasal_freq: ClassVar[float] = 1200.0
    nasal_q: ClassVar[float] = 3.0
    nasal_gain: ClassVar[float] = 2.0

    partial_pitches: list[PyoObject]
    partial_levels: list[SigTo]
    partial_gains: list[PyoObject]
    partial_tones: list[Sine]
    nasal_amount: SigTo
    nasal_level: PyoObject
    nasal_band: Reson
    nasal_sum: PyoObject

    @Param(
        0,
        1,
        0.05,
        0.5,
        "Bore",
        "The shape of the pipe; none is a straight tube that keeps only the odd harmonics, a hollow, woody tone, a lot is a cone that keeps them all, a fuller, more nasal one. The loudness stays put.",
        sweep=True,
    )
    def cone(self, value: float) -> None:
        self.shape_partials()

    @Param(
        0,
        1,
        0.05,
        0.6,
        "Reed edge",
        "How hard the reed buzzes; low is a soft, rounded reed with few harmonics, high is a hard, biting one with many. The loudness stays put.",
        sweep=True,
    )
    def edge(self, value: float) -> None:
        self.shape_partials()

    nasal = Param(
        0,
        1,
        0.05,
        0,
        "Nasal",
        "The pinched ring of a double reed's bell; none is a plain, even tone, a lot is a reedy, nasal, plaintive one.",
        sweep=True,
    )

    def shape_partials(self) -> None:
        """Set every harmonic's level from `Bore` and `Reed edge` together, so
        the first picks which harmonics exist and the second how loud each is;
        the whole is normalised to one loudness."""
        slope = self.soft_slope + (self.buzz_slope - self.soft_slope) * self.edge
        weights = [
            (number**-slope) * (1.0 if number % 2 else self.cone)
            for number in range(1, self.partials + 1)
        ]
        norm = sum(weight**2 for weight in weights) ** 0.5
        for level, weight in zip(self.partial_levels, weights, strict=True):
            level.value = weight / norm

    def make_source(self) -> PyoObject:
        self.partial_pitches = [
            self.held_pitch * number for number in range(1, self.partials + 1)
        ]
        self.partial_levels = [
            SigTo(value=0, time=self.level_glide) for _ in range(self.partials)
        ]
        self.partial_gains = [
            self.voice_gain * (level * self.tone_level) for level in self.partial_levels
        ]
        self.partial_tones = [
            Sine(freq=pitch, mul=gain)
            for pitch, gain in zip(
                self.partial_pitches, self.partial_gains, strict=True
            )
        ]
        self.retain(
            *self.partial_pitches,
            *self.partial_levels,
            *self.partial_gains,
            *self.partial_tones,
        )
        return Mix(self.partial_tones, voices=1)

    def voice_stage(self, signal: PyoObject) -> PyoObject:
        cls = type(self)
        # the bell's ring, added to the tone ahead of the pipe so Brightness
        # and Pitch tracking close over it too
        self.nasal_amount = self.live(cls.nasal)
        self.nasal_level = self.nasal_amount * self.nasal_gain
        self.nasal_band = Reson(
            signal, freq=self.nasal_freq, q=self.nasal_q, mul=self.nasal_level
        )
        self.nasal_sum = signal + self.nasal_band
        return super().voice_stage(self.nasal_sum)
