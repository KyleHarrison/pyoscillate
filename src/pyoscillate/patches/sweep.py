"""A `Param` that moves by itself: a bouncing sweep between a low and a high.

A `Param` declared with `sweep=True` gets one `Sweep` per patch instance. While
enabled and the patch is playing, a pyo triangle `LFO` runs at one full
low -> high -> low cycle per `bars` bars, and a pyo `Pattern` samples it and
pushes the mapped value through the parameter's own control. The value the
user set (`patch.<param>`) is never overwritten: it stays the resting value
the sweep hands back when it is switched off, and what a preset stores.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from pyo.lib.generators import LFO
from pyo.lib.pattern import Pattern

from pyoscillate.patches.params import Param

if TYPE_CHECKING:
    from pyoscillate.patches.base import Patch


@dataclass(frozen=True, eq=False)
class ParamSweep:
    """A rack's declaration of a starting sweep on a patch's `Param`: between
    `low` and `high`, one full there-and-back cycle every `bars` bars. A
    `Slot` turns it on for the patch it binds."""

    param: Param
    low: float
    high: float
    bars: float = 8.0


class Sweep:
    """One parameter's sweep on one patch: its settings (`enabled`, `low`,
    `high`, `bars`) and, while running, the pyo `LFO` and `Pattern` driving
    it. Settings survive rebuilds and stops; the pyo objects exist only from
    `run()` to `halt()`."""

    DEFAULT_BARS: ClassVar[float] = 8.0
    MIN_BARS: ClassVar[float] = 1.0
    MAX_BARS: ClassVar[float] = 64.0
    # seconds between pushes of the sampled value into the parameter
    REFRESH: ClassVar[float] = 0.05

    lfo: LFO
    pattern: Pattern

    def __init__(self, patch: Patch, param: Param) -> None:
        self.patch = patch
        self.param = param
        self.enabled = False
        # a sweep starts pinned at the parameter's default, so switching it
        # on changes nothing until the limits are pulled apart
        self.low = param.spec.default
        self.high = param.spec.default
        self.bars = self.DEFAULT_BARS
        self._running = False

    @property
    def running(self) -> bool:
        return self._running

    def declare(self, sweep: ParamSweep) -> None:
        """Adopt a rack's declared sweep and switch it on."""
        self.enabled = True
        self.configure(sweep.low, sweep.high, sweep.bars)

    def configure(self, low: float, high: float, bars: float) -> None:
        """Set the range (kept inside the parameter's slider range, low <=
        high) and the cycle length; a running sweep retunes immediately."""
        spec = self.param.spec
        low, high = sorted((low, high))
        self.low = min(max(low, spec.minimum), spec.maximum)
        self.high = min(max(high, spec.minimum), spec.maximum)
        self.bars = min(max(bars, self.MIN_BARS), self.MAX_BARS)
        if self._running:
            self.lfo.freq = self._frequency()

    def value_at(self, position: float) -> float:
        """The parameter value `position` (0 = low, 1 = high) along the range."""
        return self.low + position * (self.high - self.low)

    @property
    def position(self) -> float:
        """Where the running sweep is between low (0) and high (1); 0 when
        it isn't running."""
        if not self._running:
            return 0.0
        return min(max(float(self.lfo.get()), 0.0), 1.0)

    @property
    def value(self) -> float:
        """The value the graph is using: the sweep's current one while
        running, otherwise the parameter's resting value."""
        if self._running:
            return self.value_at(self.position)
        return self.param.read(self.patch)

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        if enabled:
            if self.patch.playing:
                self.run()
        else:
            self.halt()
            if self.patch.built:
                self.patch.apply_param(self.param, self.param.read(self.patch))

    def run(self) -> None:
        """Start driving the parameter, if enabled, not already running, and
        the patch was started with a tempo to sync to."""
        if not self.enabled or self._running or self.patch.tempo is None:
            return
        self.lfo = LFO(freq=self._frequency(), type=3, sharp=1, mul=0.5, add=0.5)
        self.pattern = Pattern(self.push, time=self.REFRESH)
        self.pattern.play()
        self._running = True

    def halt(self) -> None:
        """Stop driving the parameter. The pyo objects are stopped but kept
        until the next `run()` replaces them, so they are never collected
        while still active."""
        if not self._running:
            return
        self._running = False
        self.pattern.stop()
        self.lfo.stop()

    def push(self) -> None:
        self.patch.apply_param(self.param, self.value_at(self.position))

    def _frequency(self) -> float:
        assert self.patch.tempo is not None
        return 1 / (self.bars * self.patch.tempo.bar)
