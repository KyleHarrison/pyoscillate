"""Opt-in effect add-ons: `Comb`, `Disperse` and `Flood` (see
`patches/AGENTS.md`, "Effect add-ons"). Each is a mixin that owns its `Param`s
and an `add_*(source)` helper returning the processed signal; a voice mixes in
the ones it wants and chains them in `build()` before its gate.

Every effect is always built and its amount `Param` defaults to 0, so adding
one changes nothing until a rack or listener raises it, and the amount never
needs a rebuild.
"""

from __future__ import annotations

from typing import ClassVar

from pyo import PyoObject
from pyo.lib.effects import Delay, Freeverb, Waveguide

from pyoscillate.patches.base import Patch
from pyoscillate.patches.params import Param
from pyoscillate.theory import notes


class Comb(Patch):
    """Tuned feedback comb: the sound rings through a short resonant delay
    (pyo `Waveguide`) so partials near multiples of the comb pitch ring on,
    giving a hollow, pitched, metallic edge. `comb` is how much of the ringing
    is mixed in alongside the dry sound."""

    COMB_GAIN: ClassVar[float] = 0.5

    comb_wave: Waveguide
    comb_output: PyoObject

    @Param(
        0.0,
        1.0,
        0.05,
        0.0,
        "Comb",
        "Mixes in a hollow, pitched ringing that follows the sound; zero is untouched, full is a "
        "metallic, resonant tone around the Comb pitch.",
        sweep=True,
    )
    def comb(self, value: float) -> None:
        self.comb_wave.mul = value * self.COMB_GAIN

    comb_pitch = Param(
        notes.A2,
        notes.A4,
        1,
        notes.A3,
        "Comb pitch",
        "The note the ringing is tuned to; low is a deep, boxy resonance, high a thin, glassy one.",
        scale="note",
    )

    @Param(
        0.05,
        2.0,
        0.05,
        0.5,
        "Comb ring",
        "How long the ringing lasts, in seconds; short is a tight metallic tick, long a sustained "
        "tuned drone.",
    )
    def comb_ring(self, value: float) -> None:
        self.comb_wave.dur = value

    def add_comb(self, source: PyoObject) -> PyoObject:
        """`source` plus its tuned ringing; call in `build()` before `finish()`."""
        self.comb_wave = Waveguide(source, freq=self.comb_pitch, dur=self.comb_ring)
        self.comb_output = source + self.comb_wave
        return self.comb_output


class Disperse(Patch):
    """Delay-cluster smear: several feedback delays at unrelated times (a
    prime-ish spread) summed behind the sound, so each event is blurred into a
    diffuse, shimmering cloud rather than discrete echoes."""

    # the delay times as multiples of the base spread, deliberately unrelated
    DISPERSE_TIMES: ClassVar[tuple[float, ...]] = (1.0, 1.31, 1.73, 2.19)
    DISPERSE_FEEDBACK: ClassVar[float] = 0.55
    DISPERSE_MAX_DELAY: ClassVar[float] = 2.5

    disperse_taps: list[Delay]
    disperse_output: PyoObject

    @Param(
        0.0,
        1.0,
        0.05,
        0.0,
        "Disperse",
        "Smears the sound into a diffuse, shimmering cloud behind it; zero is dry, full blurs "
        "every hit into a wash.",
        sweep=True,
    )
    def disperse(self, value: float) -> None:
        level = value / len(self.DISPERSE_TIMES) ** 0.5
        for tap in self.disperse_taps:
            tap.mul = level

    @Param(
        0.01,
        0.5,
        0.01,
        0.08,
        "Disperse spread",
        "How far apart the smeared repeats sit, in seconds; short is a tight, grainy blur, long a "
        "spacious, rolling cloud.",
    )
    def disperse_spread(self, value: float) -> None:
        for tap, ratio in zip(self.disperse_taps, self.DISPERSE_TIMES):
            tap.delay = value * ratio

    def add_disperse(self, source: PyoObject) -> PyoObject:
        """`source` plus its smear; call in `build()` before `finish()`."""
        self.disperse_taps = [
            Delay(
                source,
                delay=0.1 * ratio,
                feedback=self.DISPERSE_FEEDBACK,
                maxdelay=self.DISPERSE_MAX_DELAY,
                mul=0,
            )
            for ratio in self.DISPERSE_TIMES
        ]
        self.disperse_output = source + sum(
            self.disperse_taps[1:], self.disperse_taps[0]
        )
        return self.disperse_output


class Flood(Patch):
    """Wet-dominant reverb macro: one amount raises the room size and the wet
    share together, so the dry sound is pushed back as the amount rises until
    only the wash remains. (Plain reverb adds a tail to a dry sound; flood
    drowns it.)"""

    FLOOD_SIZE_MIN: ClassVar[float] = 0.5
    FLOOD_SIZE_MAX: ClassVar[float] = 0.95
    FLOOD_DAMP: ClassVar[float] = 0.5

    flood_verb: Freeverb

    @Param(
        0.0,
        1.0,
        0.05,
        0.0,
        "Flood",
        "Drowns the sound in a huge room; zero is dry, full pushes the original far back until only "
        "a long, washed-out tail is left.",
        sweep=True,
    )
    def flood(self, value: float) -> None:
        self.flood_verb.bal = value
        self.flood_verb.size = (
            self.FLOOD_SIZE_MIN + (self.FLOOD_SIZE_MAX - self.FLOOD_SIZE_MIN) * value
        )

    def add_flood(self, source: PyoObject) -> PyoObject:
        """`source` through the flood reverb; call in `build()` before `finish()`."""
        self.flood_verb = Freeverb(source, damp=self.FLOOD_DAMP)
        return self.flood_verb
