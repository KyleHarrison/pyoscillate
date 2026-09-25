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
(`patches/CLAUDE.md`'s design rule 1).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, ClassVar

from pyo import PyoObject
from pyo.lib.filters import ComplexRes
from pyo.lib.generators import FM
from pyo.lib.tables import LinTable
from pyo.lib.triggers import Trig, TrigEnv

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.patches.base import Patch
from pyoscillate.patches.common import RING_CURVE, decay_points
from pyoscillate.patches.params import SliderSpec
from pyoscillate.patches.utility.notes import notes
from pyoscillate.tempo import Tempo

STYLES = ("chime", "fm")
BASE_DIVISION = NoteDivision.SIXTEENTH

PARAMETERS = (
    SliderSpec(
        "root_freq",
        notes.A3,
        notes.A5,
        1,
        notes.A4,
        "Register",
        "Moves the bell figure up or down; low reads as a church bell or gong, high as a glockenspiel or chime.",
        scale="note",
    ),
    SliderSpec(
        "strike",
        0,
        1,
        0.05,
        0.6,
        "Strike",
        "How hard the bell is hit: soft is a round, mellow tone, hard adds a bright, clanging edge to the start of each note.",
    ),
    SliderSpec(
        "ring",
        0.3,
        6,
        0.1,
        2.5,
        "Ring",
        "How long each note rings, in seconds, before it fades out; long rings overlap into a shimmering wash.",
    ),
    SliderSpec(
        "rate",
        Clock.rate_limits(BASE_DIVISION)[0],
        Clock.rate_limits(BASE_DIVISION)[1],
        1,
        0,
        "Rate",
        "Halves or doubles the speed of the bell figure for each step away from its 16th-note grid.",
    ),
)
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
VOLUME_DEFAULT = 0.35


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
    mid-ring. Style variants subclass this and override `voice_graph()`;
    the pattern stepping and voice rotation are identical."""

    parameters = PARAMETERS
    volume_default = VOLUME_DEFAULT
    needs_tempo: ClassVar[bool] = True
    needs_clock: ClassVar[bool] = True

    root_freq: float
    strike: float
    ring: float
    rate: float

    def _reset(self) -> None:
        super()._reset()
        self.triggers = [Trig().stop() for _ in range(VOICES)]
        self.retain(*self.triggers)

    def voice_graph(
        self,
    ) -> tuple[
        PyoObject, Callable[[int, float], None], dict[str, Callable[[Any], None]], tuple[Any, ...]
    ]:
        """This style's resonance graph, built from `self.triggers`: the
        summed voice, a `tune(slot, freq)` callback the shared pattern
        stepper calls on each hit, this style's Strike/Ring live controls,
        and any extra Pyo objects to retain. Overridden per style."""
        raise NotImplementedError

    def build(self, tempo: Tempo, clock: Clock, **values: Any) -> Patch:
        del (
            tempo
        )  # deliberately free of the tempo grid's own note values; PATTERN still rides the clock
        self.configure(**values)
        self._reset()

        voice, tune, controls, resources = self.voice_graph()
        self.retain(*resources)

        state = {"step": 0, "voice": 0, "root": self.root_freq}

        def next_step() -> None:
            semitones = PATTERN.get(state["step"] % PATTERN_STEPS)
            if semitones is not None:
                slot = state["voice"]
                tune(slot, state["root"] * 2 ** (semitones / 12))
                self.triggers[slot].play()
                state["voice"] = (slot + 1) % VOICES
            state["step"] += 1

        division = clock.subscribe(clock.ticks_for_rate(BASE_DIVISION, self.rate), next_step)
        self.sequencer = division
        self.voice = voice
        self.controls = {
            **controls,
            "root_freq": lambda value: state.update(root=value),
            "rate": lambda value: setattr(
                division, "steps", clock.ticks_for_rate(BASE_DIVISION, value)
            ),
        }
        return self


class BellChime(Bell):
    """Modal bell: an impulse into a `ComplexRes` bank of church-bell partials."""

    title = "Bell - Chime"

    def voice_graph(self):
        excitation = [trigger for trigger in self.triggers for _ in PARTIALS]
        freqs = [self.root_freq * ratio for _ in range(VOICES) for ratio in PARTIALS]
        bank = ComplexRes(
            excitation,
            freq=freqs,
            decay=_chime_decays(self.ring) * VOICES,
            mul=_chime_gains(self.strike) * VOICES,
        )
        voice = bank.mix(1)

        def tune(slot: int, freq: float) -> None:
            start = slot * len(PARTIALS)
            freqs[start : start + len(PARTIALS)] = [freq * ratio for ratio in PARTIALS]
            bank.freq = freqs

        controls = {
            "strike": lambda value: setattr(bank, "mul", _chime_gains(value) * VOICES),
            "ring": lambda value: setattr(bank, "decay", _chime_decays(value) * VOICES),
        }
        return voice, tune, controls, (bank,)


class BellFm(Bell):
    """Chowning FM bell: inharmonic ratio 1.4, index falling faster than the level."""

    title = "Bell - FM"

    def voice_graph(self):
        amp_table = LinTable(decay_points())
        index_table = LinTable(decay_points(RING_CURVE * INDEX_SPEED))
        amp = TrigEnv(self.triggers, amp_table, dur=self.ring, mul=FM_GAIN)
        index = TrigEnv(self.triggers, index_table, dur=self.ring, mul=_peak_index(self.strike))
        carriers = [self.root_freq] * VOICES
        bell = FM(carrier=carriers, ratio=FM_RATIO, index=index, mul=amp)
        voice = bell.mix(1)

        def tune(slot: int, freq: float) -> None:
            carriers[slot] = freq
            bell.carrier = carriers

        def set_ring(value: float) -> None:
            amp.dur = value
            index.dur = value

        controls = {
            "strike": lambda value: setattr(index, "mul", _peak_index(value)),
            "ring": set_ring,
        }
        return voice, tune, controls, (amp_table, index_table, amp, index, bell)
