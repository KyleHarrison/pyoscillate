# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.woodwind.lip.natural
"""Lip winds: buzzing lips on a pipe with no reed.

The lips are the valve. Their pulses carry the whole harmonic series (a
sawtooth's, whatever the bore), and how hard they buzz decides how many
harmonics there are. The pipe is long and has no tone holes, so the only
shaping is a resonance the player moves by hand and mouth: a slow sweep of
formant that makes a didgeridoo talk. `LipWind` is that source for the family:
`Buzz` sets the harmonics, `Mouth` the strength of the swept resonance and
`Mouth speed` how fast it sweeps. The partials are normalised, so neither
changes the loudness. The pipe's low-pass, tonguing, breath pulse and scoop
are `Wind`'s (see `wind.py`).
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


class LipWind(Wind):
    """A lip-driven pipe: the full harmonic series of a buzz, shaped by a
    resonance that sweeps as the player's mouth moves. A style sets the
    register, the buzz and the sweep."""

    partials: ClassVar[int] = 16
    # the slope of the harmonics' fall, 1/n to the power of this: `Buzz` moves
    # it from `soft_slope` (a soft hum) to `hard_slope` (a bright raspberry)
    soft_slope: ClassVar[float] = 2.4
    hard_slope: ClassVar[float] = 0.7
    # the range the mouth's resonance sweeps through (Hz), how sharply, and the
    # level of that ring against the tone at full Mouth
    mouth_low: ClassVar[float] = 400.0
    mouth_high: ClassVar[float] = 1800.0
    mouth_q: ClassVar[float] = 6.0
    mouth_gain: ClassVar[float] = 2.0

    partial_pitches: list[PyoObject]
    partial_levels: list[SigTo]
    partial_gains: list[PyoObject]
    partial_tones: list[Sine]
    mouth_amount: SigTo
    mouth_rate: SigTo
    mouth_level: PyoObject
    mouth_sweep: Sine
    mouth_band: Reson
    mouth_sum: PyoObject

    mouth = Param(
        0,
        1,
        0.05,
        0.5,
        "Mouth",
        "How strongly the resonance of the mouth sweeps through the tone; none is a plain buzz, a lot is a talking, vowel-like 'wah-wah' moving over the note.",
        sweep=True,
    )
    mouth_speed = Param(
        0.1,
        4,
        0.05,
        1,
        "Mouth speed",
        "How fast the mouth's resonance sweeps up and down, in cycles a second; slow is a long, rolling swell, fast is a quick, chattering 'ya-ka'.",
        sweep=True,
        advanced=True,
    )

    @Param(
        0,
        1,
        0.05,
        0.5,
        "Buzz",
        "How hard the lips buzz; low is a soft, humming tone with few harmonics, high is a bright, rasping one with many. The loudness stays put.",
        sweep=True,
    )
    def buzz(self, value: float) -> None:
        slope = self.soft_slope + (self.hard_slope - self.soft_slope) * value
        weights = [number**-slope for number in range(1, self.partials + 1)]
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
        # the mouth: a resonance swept between its low and high, added to the
        # tone ahead of the pipe
        self.mouth_amount = self.live(cls.mouth)
        self.mouth_rate = self.live(cls.mouth_speed)
        self.mouth_level = self.mouth_amount * self.mouth_gain
        self.mouth_sweep = Sine(
            freq=self.mouth_rate,
            mul=(self.mouth_high - self.mouth_low) / 2,
            add=(self.mouth_high + self.mouth_low) / 2,
        )
        self.mouth_band = Reson(
            signal, freq=self.mouth_sweep, q=self.mouth_q, mul=self.mouth_level
        )
        self.mouth_sum = signal + self.mouth_band
        return super().voice_stage(self.mouth_sum)
