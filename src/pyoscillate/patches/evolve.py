"""A patch's own evolution: every N bars its `on_evolve(index)` is called.

Each patch owns one `Evolution`. While enabled and playing it holds a clock
`Division` that fires every `bars` bars, and each fire calls the patch's
`on_evolve`. A patch that plays a `Phrase` advances to the next phrase the
listener has ticked (`Phrased.on_evolve`); any other patch overrides
`on_evolve` with its own slow change. The settings (`enabled`, `bars`, the
ticked `choices`) survive rebuilds and stops; the `Division` exists only from
`run()` to `halt()`.

Timing comes from the shared `Clock`, never an internal counter, so a change
always lands on a bar line shared with the rest of the rack and `progress`
is read straight off the clock tick.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar

from pyoscillate.clock import Clock, Division

if TYPE_CHECKING:
    from pyoscillate.patches.base import Patch


@dataclass(frozen=True, eq=False)
class Evolve:
    """A rack's declaration of a starting evolution on a patch: change every
    `bars` bars, cycling through `choices` (for a phrased patch, the phrases
    to rotate; empty keeps the patch's current choice only). A `Slot` turns it
    on for the patch it binds."""

    bars: int = 8
    choices: tuple[Any, ...] = ()


class Evolution:
    """One patch's evolution timer and the choices it rotates through."""

    DEFAULT_BARS: ClassVar[int] = 8
    MIN_BARS: ClassVar[int] = 1
    MAX_BARS: ClassVar[int] = 64

    def __init__(self, patch: Patch) -> None:
        self.patch = patch
        self.enabled = False
        self.bars = self.DEFAULT_BARS
        # the choices ticked to take part, in the patch's own order
        self.choices: tuple[Any, ...] = patch.evolution_seed()
        self._clock: Clock | None = None
        self._division: Division | None = None
        self._fires = 0

    @property
    def running(self) -> bool:
        return self._division is not None

    def declare(self, evolve: Evolve) -> None:
        """Adopt a rack's declared evolution and switch it on."""
        self.enabled = True
        self.configure(evolve.bars)
        if evolve.choices:
            self.choices = self.patch.evolution_order(evolve.choices)

    def configure(self, bars: float) -> None:
        """Set the interval in bars; a running timer retunes immediately."""
        self.bars = min(max(round(bars), self.MIN_BARS), self.MAX_BARS)
        if self._division is not None and self._clock is not None:
            self._division.steps = self._clock.bar * self.bars

    def set_choice(self, choice: Any, ticked: bool) -> None:
        """Tick or untick one choice, keeping the patch's own order."""
        chosen = {*self.choices, choice} if ticked else set(self.choices) - {choice}
        self.choices = self.patch.evolution_order(tuple(chosen))

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        if enabled:
            if self.patch.playing:
                self.run(self._clock)
        else:
            self.halt()

    def run(self, clock: Clock | None) -> None:
        """Start firing, if enabled, not already running, and the patch was
        started on a clock."""
        if clock is not None:
            self._clock = clock
        if not self.enabled or self.running or self._clock is None:
            return
        self._fires = 0
        self._division = self._clock.subscribe(self._clock.bar * self.bars, self._fire)
        self._division.play()

    def halt(self) -> None:
        if self._division is not None:
            self._division.stop()
            self._division = None

    @property
    def progress(self) -> float:
        """How far through the current interval the clock is (0 just changed,
        approaching 1 as the next change nears); 0 when not running."""
        if self._division is None or self._clock is None:
            return 0.0
        steps = self._division.steps
        return (self._clock.tick % steps) / steps

    @property
    def bars_left(self) -> float:
        """Bars until the next change; the full interval when not running."""
        return self.bars * (1 - self.progress)

    def _fire(self) -> None:
        self.patch.on_evolve(self._fires)
        self._fires += 1
