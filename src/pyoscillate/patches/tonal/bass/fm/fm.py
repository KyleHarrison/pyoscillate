# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.bass.fm.fm
"""FM bass: every note barks bright, then settles to a rounder tone.

The index follows a break-point table (pyo example x10/01's index
`LinTable` 20 → 10 → 0, scaled to 1 → 0.5 → 0) read over Settle seconds, on
top of a steady Edge floor. Accented steps scale the bark as well as the
level, so the groove's accents hit harder and brighter. That is the FM
equivalent of velocity opening the index.

- `bark`: two-operator FM (x03/03 `FM`) at integer ratio 1, so the spectrum
  stays harmonic and the note keeps a clear pitch at any index.
- `grit`: `CrossFM` (x03/03) at ratio 2. The carrier modulates the modulator
  back, which roughens the bark into a buzzier, less stable edge.

The note line is the `rolling` groove profile, on the shared clock.
"""

from __future__ import annotations

from collections.abc import Callable

from pyo.lib.controls import SigTo
from pyo.lib.filters import ButHP
from pyo.lib.generators import FM, CrossFM
from pyo.lib.tables import CosTable, LinTable
from pyo.lib.triggers import Trig, TrigEnv

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.patches.base import BuiltPatch
from pyoscillate.patches.params import PyoParamRef, SliderSpec
from pyoscillate.patches.tonal.bass.profiles import GROOVE
from pyoscillate.patches.utility.notes import notes
from pyoscillate.tempo import Tempo

STYLES = ("bark", "grit")
BASE_DIVISION = NoteDivision.SIXTEENTH
PROFILE = GROOVE["rolling"]

PARAMETERS = (
    SliderSpec(
        "root_freq",
        notes.B0,
        notes.A2,
        1,
        notes.A1,
        "Register",
        "Moves the bassline up or down; low sits under the kick as weight, high brings the bark forward as a melodic line.",
        (PyoParamRef(FM, "carrier"), PyoParamRef(CrossFM, "carrier")),
        scale="note",
    ),
    SliderSpec(
        "growl",
        0,
        12,
        0.5,
        6,
        "Growl",
        "How hard each note barks: low is a soft, round thump, high a bright, buzzing snarl at the start of every note.",
        (PyoParamRef(TrigEnv, "mul"),),
    ),
    SliderSpec(
        "settle",
        0.02,
        0.4,
        0.01,
        0.12,
        "Settle",
        "How long the bark takes to die down, in seconds: short is a quick pluck on the front of the note, long a slow, wah-like close.",
        (PyoParamRef(TrigEnv, "dur"),),
    ),
    SliderSpec(
        "edge",
        0,
        3,
        0.1,
        0.5,
        "Edge",
        "The brightness left once the bark has settled: at 0 the note settles to a pure sub, higher keeps a buzzing edge under the whole note.",
        (PyoParamRef(SigTo, "value"),),
    ),
    SliderSpec(
        "length",
        0.3,
        1.5,
        0.05,
        0.9,
        "Length",
        "How long each note lasts, in 16ths: short is tight and staccato, long runs one note into the next.",
        (PyoParamRef(TrigEnv, "dur"),),
    ),
    SliderSpec(
        "rate",
        Clock.rate_limits(BASE_DIVISION)[0],
        Clock.rate_limits(BASE_DIVISION)[1],
        1,
        0,
        "Rate",
        "Halves or doubles the bassline speed for each step away from its 16th-note grid.",
    ),
)
# x10/01's index break-points, normalised: a fast drop to half, then a
# linear fall to nothing over the rest of Settle
INDEX_POINTS = [(0, 1.0), (512, 0.5), (8191, 0.0)]
# the bass core's amplitude shape: a quick rise, a held body, then the release
AMP_POINTS = [(0, 0.0), (80, 1.0), (2100, 0.5), (8191, 0.0)]
RATIOS = {"bark": 1, "grit": 2}
# `grit`: how strongly the carrier modulates the modulator back, relative to
# the main index
CROSS = 0.5
# FM keeps a constant amplitude whatever the index, so the peak is GAIN x
# accent x volume before the subsonic high-pass, whose phase shift adds up to
# ~25% to the crest at the lowest Register
GAIN = 0.3
# under the lowest Register (30 Hz), which loses under 1 dB to it
SUBSONIC = 20
VOLUME_DEFAULT = 0.42


def _steps_for_rate(clock: Clock, rate: float) -> int:
    return clock.ticks_for_rate(BASE_DIVISION, rate)


def build(
    tempo: Tempo,
    clock: Clock,
    style: str = "bark",
    root_freq: float = notes.A1,
    growl: float = 6,
    settle: float = 0.12,
    edge: float = 0.5,
    length: float = 0.9,
    rate: float = 0,
) -> BuiltPatch:
    """Build an FM bassline whose index barks on each note; `style` picks FM or CrossFM."""
    if style not in STYLES:
        raise ValueError(f"unknown FM bass style {style!r}; expected one of {STYLES}")

    state = {"step": 0, "root": root_freq, "growl": growl, "accent": 1.0}
    trigger = Trig().stop()
    index_table = LinTable(INDEX_POINTS)
    amp_table = CosTable(AMP_POINTS)
    bark = TrigEnv(trigger, index_table, dur=settle, mul=growl)
    floor = SigTo(value=edge, time=0.05, init=edge)
    index = bark + floor
    amp = TrigEnv(trigger, amp_table, dur=tempo.sixteenth * length)
    level = amp * GAIN
    resources: list = [trigger, index_table, amp_table, bark, floor, index, amp, level]

    if style == "bark":
        tone = FM(carrier=root_freq, ratio=RATIOS[style], index=index, mul=level)
    else:
        cross = index * CROSS
        tone = CrossFM(
            carrier=root_freq, ratio=RATIOS[style], ind1=cross, ind2=index, mul=level
        )
        resources.append(cross)
    # at ratio 1 the first lower sideband lands on 0 Hz, so the bark carries a
    # DC offset that follows the index envelope: a subsonic thump that eats
    # headroom. CrossFM's feedback does the same at high index. A 2nd-order
    # high-pass below the lowest Register clears it; pyo's one-pole DCBlock
    # is too slow for an offset that moves within a few milliseconds.
    voice = ButHP(tone, freq=SUBSONIC)
    resources.append(tone)

    def next_step() -> None:
        step = state["step"] % len(PROFILE.pattern)
        state["accent"] = PROFILE.accents[step]
        tone.carrier = state["root"] * 2 ** (PROFILE.pattern[step] / 12)
        bark.mul = state["growl"] * state["accent"]
        amp.mul = state["accent"]
        trigger.play()
        state["step"] += 1

    def set_growl(value: float) -> None:
        state["growl"] = value
        bark.mul = value * state["accent"]

    division = clock.subscribe(_steps_for_rate(clock, rate), next_step)
    return BuiltPatch(
        sequencer=division,
        voice=voice,
        controls={
            "root_freq": lambda value: state.update(root=value),
            "growl": set_growl,
            "settle": lambda value: setattr(bark, "dur", value),
            "edge": lambda value: setattr(floor, "value", value),
            "length": lambda value: setattr(amp, "dur", tempo.sixteenth * value),
            "rate": lambda value: setattr(division, "steps", _steps_for_rate(clock, value)),
        },
        resources=tuple(resources),
    )


def make_builder(style: str) -> Callable[..., BuiltPatch]:
    """Return a builder with one FM bass style fixed for a rack entry."""
    return lambda **values: build(style=style, **values)
