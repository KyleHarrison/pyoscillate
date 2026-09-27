"""Clocked FM plucks with a decaying brightness envelope and short body."""

from __future__ import annotations

from typing import ClassVar

from pyo import PyoObject
from pyo.lib.controls import SigTo
from pyo.lib.effects import Freeverb
from pyo.lib.generators import FM

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import Patch
from pyoscillate.patches.common import GatedVoice
from pyoscillate.patches.params import Param, rate_param
from pyoscillate.patches.utility.notes import notes
from pyoscillate.tempo import Tempo

REST = -1
SPARSE_PATTERN = (0, REST, 1, REST, 2, REST, 1, REST)
FULL_PATTERN = (0, 1, 2, 1, 0, 2, 1, 2)


class Pluck(GatedVoice):
    """Single-note FM pluck with a fast amplitude contour and a brighter,
    quickly-decaying modulation index. Style subclasses supply the pattern."""

    needs_harmony: ClassVar[bool] = True
    volume_default = 0.4
    base_division: ClassVar[NoteDivision] = NoteDivision.EIGHTH
    gain: ClassVar[float] = 0.14
    modulator_ratio: ClassVar[float] = 2.0
    patterns: ClassVar[tuple[tuple[int, ...], ...]] = (SPARSE_PATTERN, FULL_PATTERN)
    triads: ClassVar[dict[int, tuple[int, int, int]]] = {
        0: (0, 4, 7),
        2: (0, 3, 7),
        4: (0, 3, 7),
        5: (0, 4, 7),
        7: (0, 4, 7),
        9: (0, 3, 7),
        11: (0, 3, 6),
    }

    pitch: SigTo
    amp_env: PyoObject
    brightness_env: PyoObject
    fm_voice: FM
    space: Freeverb
    harmony: Harmony | None
    _pattern: tuple[int, ...]

    root_freq = Param(
        notes.A2,
        notes.A4,
        1,
        notes.E3,
        "Register",
        "Sets the chord-root register; the plucked chord tones sound an octave above it.",
        scale="note",
    )

    @Param(
        0,
        5,
        0.1,
        2.4,
        "Brightness",
        "Sets the initial harmonic bite; the modulation naturally fades on each pluck.",
    )
    def brightness(self, value: float) -> None:
        self.brightness_env.mul = value

    @Param(
        0.1,
        1.5,
        0.05,
        0.45,
        "Decay",
        "Sets how long each plucked note rings before it falls away.",
    )
    def decay(self, value: float) -> None:
        self.amp_env.dur = value

    @Param(
        0.03,
        0.7,
        0.01,
        0.2,
        "Brightness decay",
        "Shortens or lengthens the bright attack; a shorter value makes each note softer sooner.",
    )
    def brightness_decay(self, value: float) -> None:
        self.brightness_env.dur = value

    rate = rate_param(
        base_division,
        "Halves or doubles the hook's speed for each step away from its eighth-note grid.",
    )

    def _note_frequency(self, tone_index: int, bar_index: int) -> float:
        if self.harmony is None:
            root = self.root_freq
            triad = (0, 4, 7)
        else:
            degree = self.harmony.chord_offset(bar_index) % 12
            root = self.harmony.chord_freq(self.root_freq, bar_index)
            triad = self.triads.get(degree, (0, 4, 7))
        return root * 2 ** ((12 + triad[tone_index]) / 12)

    def on_evolve(self, index: int) -> None:
        self._pattern = self.patterns[index % len(self.patterns)]

    def build(self, tempo: Tempo, clock: Clock, harmony: Harmony | None = None) -> Patch:
        self._reset()
        self.harmony = harmony
        self._pattern = self.patterns[0]

        initial_frequency = self._note_frequency(0, clock.bar_index)
        self.pitch = SigTo(value=initial_frequency, time=0.01)
        self.amp_env = self.envelope([(0, 0), (80, 1), (8191, 0)], dur=self.decay, exp=3)
        self.brightness_env = self.envelope(
            [(0, 1), (8191, 0)], dur=self.brightness_decay, mul=0, exp=3
        )
        self.fm_voice = FM(
            carrier=self.pitch,
            ratio=self.modulator_ratio,
            index=self.brightness_env,
            mul=self.amp_env * self.gain,
        )
        self.space = Freeverb(self.fm_voice, size=0.35, damp=0.55, bal=0.22)

        self.schedule(self.base_division, self.rate, clock)
        return self.finish(self.space)

    def next_step(self) -> None:
        step = (self._clock.tick // self._division.steps) % len(self._pattern)
        tone_index = self._pattern[step]
        if tone_index == REST:
            self.amp_env.stop()
            self.brightness_env.stop()
            return

        self.pitch.value = self._note_frequency(tone_index, self._clock.bar_index)
        self.trigger.play()


class PluckHook(Pluck):
    """Soft, sparse-to-full chord-tone hook in the middle and upper register."""

    title = "Hook - Pluck"
    summary = "Soft FM pluck tracing the shared chord tones above the bass and pad."
