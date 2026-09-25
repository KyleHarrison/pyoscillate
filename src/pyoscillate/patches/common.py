from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from pyo import PyoObject
from pyo.lib.filters import Hilbert
from pyo.lib.generators import Sine

from pyoscillate.patches.base import Sequencer


@dataclass(eq=False)
class ContinuousSequencer:
    """No-op `Sequencer` for psyambient's purely continuous, non-triggered patches.

    These pads are wired entirely from free-running modulators (chaotic
    attractors, LFOs) feeding a generator's parameters directly - once the
    pyo objects exist they process every buffer on their own, with nothing
    that needs a `Pattern`/`Metro` to start or stop ticking. `BuiltPatch` still
    requires a `Sequencer` to call `play()`/`stop()` on, so this just
    satisfies that protocol with nothing to actually do.
    """

    def play(self) -> None:
        pass

    def stop(self) -> None:
        pass


@dataclass(eq=False)
class SequencerGroup:
    """Starts and stops several sequencers as one - for a patch whose clock
    `Division` also needs a free-running `Pattern` (for example, one that
    rewrites a table) to tick only while the patch is playing."""

    sequencers: tuple[Sequencer, ...]

    def play(self) -> None:
        for sequencer in self.sequencers:
            sequencer.play()

    def stop(self) -> None:
        for sequencer in self.sequencers:
            sequencer.stop()


@dataclass(eq=False)
class Stage:
    """A shared processing stage: its output plus every Pyo object it built,
    for the calling patch to put in its own `resources`."""

    output: PyoObject
    resources: tuple[Any, ...] = field(default=(), repr=False)


# pyo's default table length; break-point indices below are in table samples
TABLE_SIZE = 8192
# e-folds across a decay table: exp(-ln 100) is -40 dB, the level where a
# struck tone reads as gone, so a reader's `dur` is the audible ring time
RING_CURVE = math.log(100)


def decay_points(
    curve: float = RING_CURVE,
    *,
    attack: int = 8,
    points: int = 24,
) -> list[tuple[int, float]]:
    """Break-points for a struck envelope: a rise over `attack` table samples,
    then an exponential fall that is `curve` e-folds down at the end, and 0.

    The shared shape of the FM family's break-point envelopes (pyo example
    x10/01). A `TrigEnv` reading it with `dur` seconds plays it at reader
    frequency 1/dur, so one table fits any note length and a live `dur`
    rescales it without rewriting the table. `TrigEnv` outputs 0 once the
    table ends, so a level that should remain after the fall has to be added
    separately.
    """
    span = TABLE_SIZE - 1 - attack
    fall = [
        (attack + round(span * step / points), math.exp(-curve * step / points))
        for step in range(points)
    ]
    return [(0, 0.0), *fall, (TABLE_SIZE - 1, 0.0)]


def frequency_shift(source: PyoObject, shift: Any) -> Stage:
    """Single-sideband frequency shift: every partial moves by `shift` Hz.

    From the pyo Hilbert example (x06/07): the Hilbert transform splits the
    source into two signals 90 degrees apart, and multiplying them by a
    quadrature sine/cosine pair keeps only the sum sideband. Unlike a pitch
    shift the partials move by a fixed amount, not a ratio, so harmonic
    spacing is lost - small shifts read as slow phasing against the dry
    sound, larger ones as inharmonic, metallic detune. A negative `shift`
    moves the spectrum down.
    """
    hilbert = Hilbert(source)
    # streams [sine, cosine]: phase 0.25 of a cycle is the cosine
    quadrature = Sine(freq=shift, phase=[0, 0.25])
    real_part = hilbert["real"] * quadrature[1]
    imaginary_part = hilbert["imag"] * quadrature[0]
    shifted = real_part + imaginary_part
    return Stage(shifted, (hilbert, quadrature, real_part, imaginary_part))
