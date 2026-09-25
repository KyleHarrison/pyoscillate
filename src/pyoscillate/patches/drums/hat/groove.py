# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.drums.hat.groove style=crisp
#   style: crisp | open | shuffle
"""Groove hi-hat voices with closed and open articulations.

The source blends white noise with a cluster of high FM operators at
inharmonic ratios (a dense metallic spectrum), high-passed out of the kick and
bass range. Each
hit is either closed or open: both share one exponential envelope, so a closed
hit retriggers it and chokes any open tail still ringing.
"""

from typing import Any, ClassVar

from pyo.lib._core import Mix
from pyo.lib.filters import ButHP
from pyo.lib.generators import FM, Noise
from pyo.lib.pan import Selector

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.patches.base import Patch
from pyoscillate.patches.drums.base import DrumVoice
from pyoscillate.patches.params import SliderSpec, rate_slider
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
    rate_slider(
        BASE_DIVISION,
        "Halves or doubles the hat pattern speed for each step away from its 16th-note grid.",
    ),
)
CLOSED = "closed"
OPEN = "open"
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


class Groove(DrumVoice):
    """Grid-locked hat pattern with closed/open choke: one shared envelope
    whose duration is reassigned per hit to the firing articulation, so a
    closed hit retriggering it cuts off any still-ringing open tail. Style
    variants share this behavior and override only which steps fire and
    with which articulation.
    """

    parameters = PARAMETERS
    volume_default = VOLUME_DEFAULT

    level: float
    cutoff: float
    metal: float
    length: float
    rate: float

    # step in the 16-step bar -> which articulation plays there - overridden
    # per style
    pattern: ClassVar[dict[int, str]]

    def build(self, tempo: Tempo, clock: Clock, **values: Any) -> Patch:
        """Build a style-specific, grid-locked hat pattern with closed/open choke."""
        self.configure(**values)
        self._reset()
        envelope = self.envelope(
            [(0, 1), (8191, 0)], dur=DURATIONS[CLOSED] * self.length, mul=self.level, exp=DECAY_CURVE
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
        source = Selector([noise, cluster], voice=self.metal)
        shaped = source * envelope
        voice = ButHP(shaped, freq=self.cutoff)
        self.retain(noise, *operators, cluster, source, shaped)
        state = {"level": self.level, "length": self.length}

        step = self.step_pattern(16, self.pattern)

        def next_step() -> None:
            step_index, articulation = step()
            if articulation is not None:
                accent = OFFBEAT_ACCENT if step_index % 4 == 2 else GHOST_ACCENT
                envelope.mul = state["level"] * accent
                # one envelope for both articulations, so a closed hit
                # restarting it cuts off an open tail - the hat choke
                envelope.dur = DURATIONS[articulation] * state["length"]
                self.trigger.play()

        def set_level(value: float) -> None:
            state["level"] = value
            envelope.mul = value

        def set_length(value: float) -> None:
            state["length"] = value

        self.schedule(BASE_DIVISION, self.rate, clock, next_step)
        return self.finish(
            voice,
            {
                "level": set_level,
                "cutoff": lambda value: setattr(voice, "freq", value),
                "metal": lambda value: setattr(source, "voice", value),
                "length": set_length,
            },
        )


class GrooveCrisp(Groove):
    """Tight, crisp top-end pulse."""

    name = "hat_crisp"
    title = "Hat - Crisp"
    pattern: ClassVar[dict[int, str]] = {2: CLOSED, 6: CLOSED, 10: CLOSED, 14: CLOSED}


class GrooveOpen(Groove):
    """Airier, more open top-end texture with longer tails."""

    name = "hat_open"
    title = "Hat - Open"
    pattern: ClassVar[dict[int, str]] = {2: OPEN, 6: OPEN, 10: OPEN, 14: OPEN, 15: CLOSED}


class GrooveShuffle(Groove):
    """Loosely shuffled, syncopated top-end groove."""

    name = "hat_shuffle"
    title = "Hat - Shuffle"
    pattern: ClassVar[dict[int, str]] = {
        2: CLOSED,
        5: CLOSED,
        6: CLOSED,
        10: CLOSED,
        13: CLOSED,
        14: OPEN,
    }
