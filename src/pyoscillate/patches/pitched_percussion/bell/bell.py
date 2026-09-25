# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.pitched_percussion.bell.bell
"""Struck bell: a two-bar pentatonic figure rung on inharmonic partials.

Two strategies share one control surface, so a rack can swap them:

- `chime`: modal. Each strike is a single-sample impulse into a bank of
  `ComplexRes` resonators (pyo example x06/03), one per church-bell partial.
  Each partial decays at its own rate, higher ones sooner, so the strike
  sounds metallic and then clears to the low hum. Strike tilts the impulse
  towards the upper partials, as a harder mallet does.
- `fm`: Chowning FM (x03/03) at the inharmonic ratio 1.4. Break-point
  envelopes (x10/01) drop the index faster than the level, so each note
  goes from a bright clang to a nearly pure ring. Strike sets the peak index.

Notes rotate over `VOICES` voices so a long Ring overlaps the next strike
instead of being cut or retuned mid-ring.
"""

from __future__ import annotations

from collections.abc import Callable

from pyo.lib.filters import ComplexRes
from pyo.lib.generators import FM
from pyo.lib.tables import LinTable
from pyo.lib.triggers import Trig, TrigEnv

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.patches.base import Patch
from pyoscillate.patches.common import RING_CURVE, decay_points
from pyoscillate.patches.params import PyoParamRef, SliderSpec
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
        (PyoParamRef(ComplexRes, "freq"), PyoParamRef(FM, "carrier")),
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
        (PyoParamRef(ComplexRes, "mul"), PyoParamRef(TrigEnv, "mul")),
    ),
    SliderSpec(
        "ring",
        0.3,
        6,
        0.1,
        2.5,
        "Ring",
        "How long each note rings, in seconds, before it fades out; long rings overlap into a shimmering wash.",
        (PyoParamRef(ComplexRes, "decay"), PyoParamRef(TrigEnv, "dur")),
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


def _steps_for_rate(clock: Clock, rate: float) -> int:
    return clock.ticks_for_rate(BASE_DIVISION, rate)


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


def build(
    tempo: Tempo,
    clock: Clock,
    style: str = "chime",
    root_freq: float = notes.A4,
    strike: float = 0.6,
    ring: float = 2.5,
    rate: float = 0,
) -> Patch:
    """Build a bell playing `PATTERN`; `style` picks modal or FM partials."""
    if style not in STYLES:
        raise ValueError(f"unknown bell style {style!r}; expected one of {STYLES}")

    state = {"step": 0, "voice": 0, "root": root_freq}
    triggers = [Trig().stop() for _ in range(VOICES)]
    resources: list = [*triggers]
    controls: dict[str, Callable[[float], None]] = {}

    if style == "chime":
        # one resonator stream per (voice, partial), each excited by its
        # voice's impulse
        excitation = [trigger for trigger in triggers for _ in PARTIALS]
        freqs = [root_freq * ratio for _ in range(VOICES) for ratio in PARTIALS]
        bank = ComplexRes(
            excitation,
            freq=freqs,
            decay=_chime_decays(ring) * VOICES,
            mul=_chime_gains(strike) * VOICES,
        )
        voice = bank.mix(1)
        resources += [bank]

        def tune(slot: int, freq: float) -> None:
            start = slot * len(PARTIALS)
            freqs[start : start + len(PARTIALS)] = [freq * ratio for ratio in PARTIALS]
            bank.freq = freqs

        controls["strike"] = lambda value: setattr(bank, "mul", _chime_gains(value) * VOICES)
        controls["ring"] = lambda value: setattr(bank, "decay", _chime_decays(value) * VOICES)
    else:
        amp_table = LinTable(decay_points())
        index_table = LinTable(decay_points(RING_CURVE * INDEX_SPEED))
        amp = TrigEnv(triggers, amp_table, dur=ring, mul=FM_GAIN)
        index = TrigEnv(triggers, index_table, dur=ring, mul=_peak_index(strike))
        carriers = [root_freq] * VOICES
        bell = FM(carrier=carriers, ratio=FM_RATIO, index=index, mul=amp)
        voice = bell.mix(1)
        resources += [amp_table, index_table, amp, index, bell]

        def tune(slot: int, freq: float) -> None:
            carriers[slot] = freq
            bell.carrier = carriers

        def set_ring(value: float) -> None:
            amp.dur = value
            index.dur = value

        controls["strike"] = lambda value: setattr(index, "mul", _peak_index(value))
        controls["ring"] = set_ring

    def next_step() -> None:
        semitones = PATTERN.get(state["step"] % PATTERN_STEPS)
        if semitones is not None:
            slot = state["voice"]
            tune(slot, state["root"] * 2 ** (semitones / 12))
            triggers[slot].play()
            state["voice"] = (slot + 1) % VOICES
        state["step"] += 1

    division = clock.subscribe(_steps_for_rate(clock, rate), next_step)
    controls["root_freq"] = lambda value: state.update(root=value)
    controls["rate"] = lambda value: setattr(division, "steps", _steps_for_rate(clock, value))
    return Patch(
        sequencer=division,
        voice=voice,
        controls=controls,
        resources=tuple(resources),
    )


def make_builder(style: str) -> Callable[..., Patch]:
    """Return a builder with one bell style fixed for a rack entry."""
    return lambda **values: build(style=style, **values)
