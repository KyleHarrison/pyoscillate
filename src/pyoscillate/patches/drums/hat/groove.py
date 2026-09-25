# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.drums.hat.groove style=crisp
#   style: crisp | open | shuffle
"""Groove hi-hat voices with closed and open articulations.

The source blends white noise with a cluster of high FM operators at
inharmonic ratios (a dense metallic spectrum), high-passed out of the kick and
bass range. Each
hit is either closed or open: both share one exponential envelope, so a closed
hit retriggers it and chokes any open tail still ringing.
"""

from collections.abc import Callable

from pyo.lib._core import Mix
from pyo.lib.filters import ButHP
from pyo.lib.generators import FM, Noise
from pyo.lib.pan import Selector
from pyo.lib.tables import ExpTable
from pyo.lib.triggers import Trig, TrigEnv

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.patches.base import Patch
from pyoscillate.patches.params import SliderSpec
from pyoscillate.tempo import Tempo

BASE_DIVISION = NoteDivision.SIXTEENTH

PARAMETERS = (
    SliderSpec(
        "level",
        0.02,
        0.5,
        0.01,
        0.14,
        "Presence",
        "Sets how loud and upfront the hat pattern sits in the mix.",
    ),
    SliderSpec(
        "cutoff",
        3500,
        14000,
        100,
        9000,
        "Brightness",
        "Moves the hat from fuller and closer to a hiss (lower) to thinner and airier (higher).",
    ),
    SliderSpec(
        "metal",
        0.0,
        1.0,
        0.05,
        0.35,
        "Metal",
        "Blends from a soft, breathy noise hat toward a clangy, metallic drum-machine hat.",
    ),
    SliderSpec(
        "length",
        0.5,
        2.0,
        0.05,
        1.0,
        "Length",
        "Stretches or shortens both closed and open tails together; shorter leaves more space between "
        "subdivisions, longer gives more sustained top-end lift.",
    ),
    SliderSpec(
        "rate",
        Clock.rate_limits(BASE_DIVISION)[0],
        Clock.rate_limits(BASE_DIVISION)[1],
        1,
        0,
        "Rate",
        "Halves or doubles the hat pattern speed for each step away from its 16th-note grid.",
    ),
)
CLOSED = "closed"
OPEN = "open"
# step in the 16-step bar -> which hat articulation plays there
PATTERNS = {
    "crisp": {2: CLOSED, 6: CLOSED, 10: CLOSED, 14: CLOSED},
    "open": {2: OPEN, 6: OPEN, 10: OPEN, 14: OPEN, 15: CLOSED},
    "shuffle": {2: CLOSED, 5: CLOSED, 6: CLOSED, 10: CLOSED, 13: CLOSED, 14: OPEN},
}
DURATIONS = {CLOSED: 0.1, OPEN: 0.4}
# carrier (Hz), modulator ratio, index - inharmonic ratios keep the sidebands
# from lining up into a pitch, so the cluster reads as metal, not a tone
METAL_OPERATORS = ((3400.0, 1.47, 4.0), (5250.0, 1.83, 3.0), (7150.0, 1.21, 3.0))
# after the high-pass the FM cluster sits a little below noise; this keeps
# the Metal blend roughly level-neutral
METAL_GAIN = 1.25
DECAY_CURVE = 3
OFFBEAT_ACCENT = 1.0
GHOST_ACCENT = 0.66
VOLUME_DEFAULT = 0.25


def build(
    tempo: Tempo,
    clock: Clock,
    style: str,
    level: float = 0.14,
    cutoff: float = 9000,
    metal: float = 0.35,
    length: float = 1.0,
    rate: float = 0,
) -> Patch:
    """Build a style-specific, grid-locked hat pattern with closed/open choke."""
    pattern = PATTERNS[style]
    trigger = Trig()
    envelope_table = ExpTable([(0, 1), (8191, 0)], exp=DECAY_CURVE)
    envelope = TrigEnv(
        trigger, envelope_table, dur=DURATIONS[CLOSED] * length, mul=level
    )
    noise = Noise()
    operators = tuple(
        FM(
            carrier=carrier,
            ratio=ratio,
            index=index,
            mul=METAL_GAIN / len(METAL_OPERATORS),
        )
        for carrier, ratio, index in METAL_OPERATORS
    )
    cluster = Mix(list(operators), voices=1)
    source = Selector([noise, cluster], voice=metal)
    shaped = source * envelope
    voice = ButHP(shaped, freq=cutoff)
    state = {"step": 0, "level": level, "length": length}

    def next_step() -> None:
        step = state["step"] % 16
        articulation = pattern.get(step)
        if articulation is not None:
            accent = OFFBEAT_ACCENT if step % 4 == 2 else GHOST_ACCENT
            envelope.mul = state["level"] * accent
            # one envelope for both articulations, so a closed hit
            # restarting it cuts off an open tail - the hat choke
            envelope.dur = DURATIONS[articulation] * state["length"]
            trigger.play()
        state["step"] += 1

    def set_level(value: float) -> None:
        state["level"] = value
        envelope.mul = value

    def set_length(value: float) -> None:
        state["length"] = value

    division = clock.subscribe(clock.ticks_for_rate(BASE_DIVISION, rate), next_step)
    return Patch(
        sequencer=division,
        voice=voice,
        controls={
            "level": set_level,
            "cutoff": lambda value: setattr(voice, "freq", value),
            "metal": lambda value: setattr(source, "voice", value),
            "length": set_length,
            "rate": lambda value: setattr(
                division, "steps", clock.ticks_for_rate(BASE_DIVISION, value)
            ),
        },
        resources=(
            trigger,
            envelope_table,
            envelope,
            noise,
            *operators,
            cluster,
            source,
            shaped,
        ),
    )


def make_builder(style: str) -> Callable[..., Patch]:
    """Return a builder with one hat style fixed for a rack entry."""
    return lambda tempo, clock, **values: build(tempo, clock, style, **values)
