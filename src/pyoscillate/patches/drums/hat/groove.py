# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.drums.hat.groove style=crisp
#   style: crisp | open | shuffle | lofi
"""Groove hi-hat voices with closed and open articulations.

The source blends white noise with a cluster of high FM operators at
inharmonic ratios (a dense metallic spectrum), high-passed out of the kick and
bass range. Each
hit is either closed or open: both share one exponential envelope, so a closed
hit retriggers it and chokes any open tail still ringing.

`pattern`'s value is either a bare articulation string (the accent for that
step falls back to `offbeat_accent`/`ghost_accent` by its position in the bar)
or an `(articulation, accent)` pair for a style, like `GrooveLofi`, that needs
an explicit per-step ghost-note level instead of that generic guess.
`pattern_cycle` sets how many steps the pattern repeats over - 16 for a
16th-note bar, 32 for `GrooveLofi`'s 32nd-note (swung 16th) bar.
"""

from typing import ClassVar

from pyo import PyoObject
from pyo.lib._core import Mix
from pyo.lib.effects import Disto
from pyo.lib.filters import Biquad, ButHP
from pyo.lib.generators import FM, Noise
from pyo.lib.pan import Selector
from pyo.lib.triggers import TrigEnv

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.patches.base import Patch
from pyoscillate.patches.drums.base import DrumVoice
from pyoscillate.patches.params import Param, rate_param
from pyoscillate.tempo import Tempo

# full-to-zero break-points shared by the choke envelope
DROP = [(0, 1), (8191, 0)]
CLOSED = "closed"
OPEN = "open"
DURATIONS = {CLOSED: 0.1, OPEN: 0.4}
# carrier (Hz), modulator ratio, index - inharmonic ratios keep the sidebands
# from lining up into a pitch, so the cluster reads as metal, not a tone
METAL_OPERATORS = ((3400.0, 1.47, 4.0), (5250.0, 1.83, 3.0), (7150.0, 1.21, 3.0))


class Groove(DrumVoice):
    """Grid-locked hat pattern with closed/open choke: one shared envelope
    whose duration is reassigned per hit to the firing articulation, so a
    closed hit retriggering it cuts off any still-ringing open tail. Style
    variants share this behavior and override only which steps fire and
    with which articulation.
    """

    volume_default = 0.25
    base_division: ClassVar[NoteDivision] = NoteDivision.SIXTEENTH
    decay_curve: ClassVar[float] = 3
    # after the high-pass the FM cluster sits a little below noise; this
    # keeps the Metal blend roughly level-neutral
    metal_gain: ClassVar[float] = 1.25
    offbeat_accent: ClassVar[float] = 1.0
    ghost_accent: ClassVar[float] = 0.66

    # step in a `pattern_cycle`-step bar -> which articulation plays there
    # (or an explicit `(articulation, accent)` pair) - overridden per style
    pattern: ClassVar[dict[int, str | tuple[str, float]]]
    pattern_cycle: ClassVar[int] = 16

    # the graph, assigned by build(); finish() retains every one of them
    choke_env: TrigEnv
    noise: Noise
    operators: tuple[FM, ...]
    cluster: Mix
    source: Selector
    shaped: PyoObject
    filtered: ButHP

    @Param(0.02, 0.5, 0.01, 0.14, "Presence", "Sets how loud and upfront the hat pattern sits in the mix.")
    def level(self, value: float) -> None:
        self.choke_env.mul = value

    @Param(
        3500,
        14000,
        100,
        9000,
        "Brightness",
        "Moves the hat from fuller and closer to a hiss (lower) to thinner and airier (higher).",
    )
    def cutoff(self, value: float) -> None:
        self.filtered.freq = value

    @Param(
        0.0,
        1.0,
        0.05,
        0.35,
        "Metal",
        "Blends from a soft, breathy noise hat toward a clangy, metallic drum-machine hat.",
    )
    def metal(self, value: float) -> None:
        self.source.voice = value

    length = Param(
        0.5,
        2.0,
        0.05,
        1.0,
        "Length",
        "Stretches or shortens both closed and open tails together; shorter leaves more space between "
        "subdivisions, longer gives more sustained top-end lift.",
    )

    rate = rate_param(
        base_division,
        "Halves or doubles the hat pattern speed for each step away from its 16th-note grid.",
    )

    def voice_output(self) -> PyoObject:
        """Hook: the final output node after `self.filtered`. The default is
        a no-op; a style overrides this to add its own post-processing (e.g.
        a closed low-pass and light saturation for a softer voice), assigning
        any node it builds onto `self` too."""
        return self.filtered

    def build(self, tempo: Tempo, clock: Clock) -> Patch:
        """Build a style-specific, grid-locked hat pattern with closed/open choke."""
        self._reset()
        self.choke_env = self.envelope(
            DROP, dur=DURATIONS[CLOSED] * self.length, exp=self.decay_curve
        )
        self.noise = Noise()
        self.operators = tuple(
            FM(
                carrier=carrier,
                ratio=ratio,
                index=index,
                mul=self.metal_gain / len(METAL_OPERATORS),
            )
            for carrier, ratio, index in METAL_OPERATORS
        )
        self.cluster = Mix(list(self.operators), voices=1)
        self.source = Selector([self.noise, self.cluster])
        self.shaped = self.source * self.choke_env
        self.filtered = ButHP(self.shaped)

        step = self.step_pattern(self.pattern_cycle, self.pattern)

        def next_step() -> None:
            step_index, entry = step()
            if entry is not None:
                if isinstance(entry, tuple):
                    articulation, accent = entry
                else:
                    articulation = entry
                    accent = self.offbeat_accent if step_index % 4 == 2 else self.ghost_accent
                self.choke_env.mul = self.level * accent
                # one envelope for both articulations, so a closed hit
                # restarting it cuts off an open tail - the hat choke
                self.choke_env.dur = DURATIONS[articulation] * self.length
                self.trigger.play()

        self.schedule(self.base_division, self.rate, clock, next_step)
        return self.finish(self.voice_output())


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


# 32nd-note steps (`pattern_cycle` = 32, 8 per beat) -> (articulation, accent).
# Each beat's straight 16th grid (offsets 0, 2, 4, 6) keeps the downbeat and
# the "and" on the grid but delays the weak "e"/"a" 16ths by one 32nd (to 3
# and 7) for an MPC-style swing, each as a quiet ghost hit; the last "a" of
# the bar opens instead, to breathe before the loop restarts.
GROOVE_LOFI_PATTERN: dict[int, tuple[str, float]] = {
    0: (CLOSED, 1.0),
    3: (CLOSED, 0.4),
    4: (CLOSED, 0.75),
    7: (CLOSED, 0.4),
    8: (CLOSED, 0.85),
    11: (CLOSED, 0.4),
    12: (CLOSED, 0.75),
    15: (CLOSED, 0.4),
    16: (CLOSED, 1.0),
    19: (CLOSED, 0.4),
    20: (CLOSED, 0.75),
    23: (CLOSED, 0.4),
    24: (CLOSED, 0.85),
    27: (CLOSED, 0.4),
    28: (OPEN, 0.55),
}


class GrooveLofi(Groove):
    """Soft, closed-low-pass boom-bap hat: a swung 16th pattern with ghost
    notes, filtered down and lightly saturated for an 80 BPM lofi pocket
    rather than a crisp, upfront top end."""

    name = "hat_lofi"
    title = "Hat - Lofi"
    summary = "Soft, filtered boom-bap hat pattern with MPC swing and ghost notes."
    pattern: ClassVar[dict[int, tuple[str, float]]] = GROOVE_LOFI_PATTERN
    pattern_cycle: ClassVar[int] = 32
    base_division: ClassVar[NoteDivision] = NoteDivision.THIRTYSECOND
    # closes the hat's high-passed edge down into a duller, muffled top end
    lowpass_cutoff: ClassVar[float] = 6000.0
    # light saturation warms the metal/noise blend without turning it harsh
    drive: ClassVar[float] = 0.12
    cutoff = Groove.cutoff.replace(
        default=5000,
        help_text="Moves the hat from fuller and closer to a hiss (lower) to thinner and airier (higher); "
        "kept low here for a soft, muffled top end.",
    )
    metal = Groove.metal.replace(default=0.2)
    rate = rate_param(
        NoteDivision.THIRTYSECOND,
        "Halves or doubles the boom-bap hat pattern speed for each step away from its swung 32nd-note grid.",
    )

    lowpassed: Biquad
    shaper: Disto

    def voice_output(self) -> PyoObject:
        self.lowpassed = Biquad(self.filtered, freq=self.lowpass_cutoff, q=0.7, type=0)
        self.shaper = Disto(self.lowpassed, drive=self.drive, slope=0.7)
        return self.shaper
