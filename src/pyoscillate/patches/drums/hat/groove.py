# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.drums.hat.groove
#   style: crisp | open | shuffle | lofi | forest
"""Groove hi-hat voices with closed and open articulations.

The source blends white noise with a cluster of high FM operators at
inharmonic ratios (a dense metallic spectrum), high-passed out of the kick and
bass range. Each
hit is either closed or open: both share one exponential envelope, so a closed
hit retriggers it and chokes any open tail still ringing.

Each style starts on one of the shared `Rhythm` hat patterns, whose steps
carry a velocity and may be marked open; any hat can play any `Rhythm` from
its Pattern dropdown.
"""

from typing import ClassVar

from pyo import PyoObject
from pyo.lib._core import Mix
from pyo.lib.effects import Disto
from pyo.lib.filters import Biquad, ButHP
from pyo.lib.generators import FM, Noise
from pyo.lib.pan import Selector
from pyo.lib.triggers import TrigEnv

from pyoscillate.clock import NoteDivision
from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.drums.base import DROP, RhythmDrum
from pyoscillate.patches.params import Param, rate_param
from pyoscillate.theory.intervals import Rhythm

# carrier (Hz), modulator ratio, index - inharmonic ratios keep the sidebands
# from lining up into a pitch, so the cluster reads as metal, not a tone
METAL_OPERATORS = ((3400.0, 1.47, 4.0), (5250.0, 1.83, 3.0), (7150.0, 1.21, 3.0))


class Groove(RhythmDrum):
    """Grid-locked hat pattern with closed/open choke: one shared envelope
    whose duration is reassigned per hit to the firing articulation, so a
    closed hit retriggering it cuts off any still-ringing open tail. Style
    variants share this behavior and override only which steps fire and
    with which articulation.
    """

    volume = Patch.volume.replace(default=0.25)
    base_division: ClassVar[NoteDivision] = NoteDivision.SIXTEENTH
    decay_curve: ClassVar[float] = 3
    # after the high-pass the FM cluster sits a little below noise; this
    # keeps the Metal blend roughly level-neutral
    metal_gain: ClassVar[float] = 1.25
    # how long a closed and an open hit rings, before `length` stretches them
    closed_length: ClassVar[float] = 0.1
    open_length: ClassVar[float] = 0.4

    # the graph, assigned by build(); finish() retains every one of them
    choke_env: TrigEnv
    noise: Noise
    operators: tuple[FM, ...]
    cluster: Mix
    source: Selector
    shaped: PyoObject
    filtered: ButHP

    @Param(
        0.02,
        0.5,
        0.01,
        0.14,
        "Presence",
        "Sets how loud and upfront the hat pattern sits in the mix.",
    )
    def level(self, value: float) -> None:
        self.choke_env.mul = value

    @Param(
        3500,
        14000,
        100,
        9000,
        "Brightness",
        "Moves the hat from fuller and closer to a hiss (lower) to thinner and airier (higher).",
        sweep=True,
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
        sweep=True,
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
        sweep=True,
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

    def build(self, context: BuildContext) -> Patch:
        """Build a style-specific, grid-locked hat pattern with closed/open choke."""
        self._reset()
        self.choke_env = self.envelope(
            DROP, dur=self.closed_length * self.length, exp=self.decay_curve
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

        self.schedule_pattern(context)
        return self.finish(self.voice_output())

    def next_step(self) -> None:
        step = self._step()
        if step.hit:
            opened = step.index in self.selected_rhythm.open_steps
            self.choke_env.mul = self.level * step.value
            # one envelope for both articulations, so a closed hit
            # restarting it cuts off an open tail - the hat choke
            self.choke_env.dur = (
                self.open_length if opened else self.closed_length
            ) * self.length
            self.trigger.play()


class GrooveCrisp(Groove):
    """Tight, crisp top-end pulse."""

    name = "hat_crisp"
    title = "Hat - Crisp"
    rhythm = Groove.rhythm.replace(default=Rhythm.HAT_CRISP.index)


class GrooveOpen(Groove):
    """Airier, more open top-end texture with longer tails."""

    name = "hat_open"
    title = "Hat - Open"
    rhythm = Groove.rhythm.replace(default=Rhythm.HAT_OPEN.index)


class GrooveShuffle(Groove):
    """Loosely shuffled, syncopated top-end groove."""

    name = "hat_shuffle"
    title = "Hat - Shuffle"
    rhythm = Groove.rhythm.replace(default=Rhythm.HAT_SHUFFLE.index)


class GrooveForest(Groove):
    """Subtle psytrance hat: quiet open offbeats on each "&" choked by softer
    closed ghosts on the "a", so the hat stays a background shimmer around
    the kick/bass pocket instead of an accent."""

    name = "hat_forest"
    title = "Hat - Forest"
    summary = (
        "Quiet open offbeat hats choked by soft closed ghosts; a background shimmer."
    )
    rhythm = Groove.rhythm.replace(default=Rhythm.HAT_FOREST.index)
    cutoff = Groove.cutoff.replace(default=8000)
    metal = Groove.metal.replace(default=0.5)
    length = Groove.length.replace(default=0.7)


class GrooveLofi(Groove):
    """Soft, closed-low-pass boom-bap hat: a swung 16th pattern with ghost
    notes, filtered down and lightly saturated for an 80 BPM lofi pocket
    rather than a crisp, upfront top end."""

    name = "hat_lofi"
    title = "Hat - Lofi"
    summary = "Soft, filtered boom-bap hat pattern with MPC swing and ghost notes."
    rhythm = Groove.rhythm.replace(default=Rhythm.HAT_LOFI.index)
    # the rhythms `on_evolve` rotates through
    variants: ClassVar[tuple[Rhythm, ...]] = (Rhythm.HAT_LOFI, Rhythm.HAT_LOFI_FULL)
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

    def on_evolve(self, index: int) -> None:
        self.rhythm = self.variants[index % len(self.variants)].index
