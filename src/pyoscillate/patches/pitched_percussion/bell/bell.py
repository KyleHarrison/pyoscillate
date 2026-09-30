# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.pitched_percussion.bell.bell
"""Struck bell: a two-bar pentatonic figure rung on inharmonic partials.

Two strategies share one control surface, so a rack can swap them:

- `chime` (`BellChime`): modal. Each strike is a single-sample impulse into a
  bank of `ComplexRes` resonators (pyo example x06/03), one per church-bell
  partial. Each partial decays at its own rate, higher ones sooner, so the
  strike sounds metallic and then clears to the low hum. Strike tilts the
  impulse towards the upper partials, as a harder mallet does.
- `fm` (`BellFm`): Chowning FM (x03/03) at the inharmonic ratio 1.4.
  Break-point envelopes (x10/01) drop the index faster than the level, so
  each note goes from a bright clang to a nearly pure ring. Strike sets the
  peak index.

Notes rotate over `VOICES` voices so a long Ring overlaps the next strike
instead of being cut or retuned mid-ring. Both styles share that rotation
(`Bell.build`); only the resonance graph in `voice_graph()` differs, since
that is genuinely different behavior, not just different profile data
(`patches/AGENTS.md`'s design rule 3).
"""

from __future__ import annotations

from typing import ClassVar

from pyo import PyoObject
from pyo.lib.filters import ComplexRes
from pyo.lib.generators import FM
from pyo.lib.tables import LinTable
from pyo.lib.triggers import Trig, TrigEnv

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.common import RING_CURVE, decay_points
from pyoscillate.patches.params import Param, rate_param
from pyoscillate.patches.utility.notes import notes

STYLES = ("chime", "fm")
BASE_DIVISION = NoteDivision.SIXTEENTH

# step on the 16th grid -> semitones above Register: two bars of minor pentatonic
PATTERN = {0: 12, 6: 7, 12: 10, 16: 3, 22: 5, 28: 0}
PATTERN_STEPS = 32
VOICES = 3
# `chime`: church-bell partials relative to the prime (the pitch the ear
# names): hum, prime, tierce, quint, nominal, then the upper partials
PARTIALS = (0.5, 1.0, 1.2, 1.5, 2.0, 2.5, 2.67, 3.0, 4.0)
# each partial's ring is Ring x ratio^-DECAY_SLOPE: the hum outlasts the
# prime, the top partial is gone in half the time
DECAY_SLOPE = 0.5
# a soft strike weights the partials by ratio^-TILT (dark, hum-heavy); a hard
# strike weights them evenly
TILT = 2.0
# an impulse leaves each resonator ringing at about 1% of full scale; brings
# the bank up to the fm style's loudness
CHIME_GAIN = 14.0
# `fm`: Chowning's bell, modulator = 1.4 x carrier
FM_RATIO = 1.4
# the peak index spans this range across Strike
INDEX_RANGE = (1.5, 12.0)
# the index table falls this many times faster than the level, so the
# brightness clears while the tone still rings (CCRMA's tubular bell)
INDEX_SPEED = 2.5
FM_GAIN = 0.2


def _chime_gains(strike: float) -> list[float]:
    """Per-partial strike weights, scaled so their total power is constant."""
    tilt = TILT * (1 - strike)
    weights = [ratio**-tilt for ratio in PARTIALS]
    norm = sum(weight**2 for weight in weights) ** 0.5
    return [CHIME_GAIN * weight / norm for weight in weights]


def _chime_decays(ring: float) -> list[float]:
    """ComplexRes time constants: Ring is the prime's time to -40 dB."""
    return [ring / RING_CURVE * ratio**-DECAY_SLOPE for ratio in PARTIALS]


def _peak_index(strike: float) -> float:
    low, high = INDEX_RANGE
    return low + (high - low) * strike


class Bell(Patch):
    """Struck bell playing `PATTERN` across `VOICES` rotating voices, so a
    long ring overlaps the next strike instead of being cut or retuned
    mid-ring. Style variants subclass this and override `voice_graph()`,
    `set_strike()` and `set_ring()`; the pattern stepping and voice rotation
    are identical."""

    volume = Patch.volume.replace(default=0.35)
    base_division: ClassVar[NoteDivision] = NoteDivision.SIXTEENTH

    triggers: list[Trig]
    voice_signal: PyoObject
    _clock: Clock
    _pattern_step: int
    _voice_slot: int

    root_freq = Param(
        notes.A3,
        notes.A5,
        1,
        notes.A4,
        "Register",
        "Moves the bell figure up or down; low reads as a church bell or gong, high as a glockenspiel or chime.",
        scale="note",
    )

    @Param(
        0,
        1,
        0.05,
        0.6,
        "Strike",
        "How hard the bell is hit: soft is a round, mellow tone, hard adds a bright, clanging edge to the start of each note.",
    )
    def strike(self, value: float) -> None:
        self.set_strike(value)

    @Param(
        0.3,
        6,
        0.1,
        2.5,
        "Ring",
        "How long each note rings, in seconds, before it fades out; long rings overlap into a shimmering wash.",
    )
    def ring(self, value: float) -> None:
        self.set_ring(value)

    rate = rate_param(
        base_division,
        "Halves or doubles the speed of the bell figure for each step away from its 16th-note grid.",
    )

    def _reset(self) -> None:
        super()._reset()
        self.triggers = [Trig().stop() for _ in range(VOICES)]
        self.retain(*self.triggers)

    def voice_graph(self) -> PyoObject:
        """This style's resonance graph, built from `self.triggers` and
        assigned to `self`, returned as the summed voice. Overridden per
        style."""
        raise NotImplementedError

    def tune(self, slot: int, freq: float) -> None:
        """Retune voice `slot` to `freq`; the shared pattern stepper calls
        this on each hit. Overridden per style."""
        raise NotImplementedError

    def set_strike(self, value: float) -> None:
        """This style's Strike control. Overridden per style."""
        raise NotImplementedError

    def set_ring(self, value: float) -> None:
        """This style's Ring control. Overridden per style."""
        raise NotImplementedError

    def build(self, context: BuildContext) -> Patch:
        self._reset()
        self._clock = context.clock
        self._pattern_step = 0
        self._voice_slot = 0

        self.voice_signal = self.voice_graph()

        self.sequencer = context.clock.subscribe(
            context.clock.ticks_for_rate(self.base_division, self.rate), self.next_step
        )
        return self.finish(self.voice_signal)

    def next_step(self) -> None:
        index = self._pattern_step % PATTERN_STEPS
        if index in PATTERN:
            slot = self._voice_slot
            self.tune(slot, self.root_freq * 2 ** (PATTERN[index] / 12))
            self.triggers[slot].play()
            self._voice_slot = (slot + 1) % VOICES
        self._pattern_step += 1

    def reschedule(self, rate: float) -> None:
        """Live `rate` control: re-space the scheduled division."""
        self.sequencer.steps = self._clock.ticks_for_rate(self.base_division, rate)

    def finish(self, voice: PyoObject) -> Patch:
        self.voice = voice
        self._bind()
        return self


class BellChime(Bell):
    """Modal bell: an impulse into a `ComplexRes` bank of church-bell partials."""

    title = "Bell - Chime"

    bank: ComplexRes
    _freqs: list[float]

    def voice_graph(self) -> PyoObject:
        excitation = [trigger for trigger in self.triggers for _ in PARTIALS]
        self._freqs = [
            self.root_freq * ratio for _ in range(VOICES) for ratio in PARTIALS
        ]
        self.bank = ComplexRes(excitation, freq=self._freqs)
        return self.bank.mix(1)

    def tune(self, slot: int, freq: float) -> None:
        start = slot * len(PARTIALS)
        self._freqs[start : start + len(PARTIALS)] = [
            freq * ratio for ratio in PARTIALS
        ]
        self.bank.freq = self._freqs

    def set_strike(self, value: float) -> None:
        self.bank.mul = _chime_gains(value) * VOICES

    def set_ring(self, value: float) -> None:
        self.bank.decay = _chime_decays(value) * VOICES


class BellFm(Bell):
    """Chowning FM bell: inharmonic ratio 1.4, index falling faster than the level."""

    title = "Bell - FM"

    amp_table: LinTable
    index_table: LinTable
    amp: TrigEnv
    index: TrigEnv
    bell: FM
    _carriers: list[float]

    def voice_graph(self) -> PyoObject:
        self.amp_table = LinTable(decay_points())
        self.index_table = LinTable(decay_points(RING_CURVE * INDEX_SPEED))
        self.amp = TrigEnv(self.triggers, self.amp_table, mul=FM_GAIN)
        self.index = TrigEnv(self.triggers, self.index_table)
        self._carriers = [self.root_freq] * VOICES
        self.bell = FM(
            carrier=self._carriers, ratio=FM_RATIO, index=self.index, mul=self.amp
        )
        return self.bell.mix(1)

    def tune(self, slot: int, freq: float) -> None:
        self._carriers[slot] = freq
        self.bell.carrier = self._carriers

    def set_strike(self, value: float) -> None:
        self.index.mul = _peak_index(value)

    def set_ring(self, value: float) -> None:
        self.amp.dur = value
        self.index.dur = value
