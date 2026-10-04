"""A patch's own evolution: slow change on its own timers, every N bars.

A patch owns one `Evolution` per thing that changes, each with its own
interval:

- an *axis* evolution moves one dropdown `Param` (the `phrase` of a `Phrased`
  patch, the `progression` of a `Progressive` one) to the next choice the
  listener has ticked, so a patch with both changes its rhythm and its chords
  on separate clocks;
- the patch's own `evolution` calls its `on_evolve(index)` hook for any other
  slow change (an inversion, a colour tone). It has no choices to tick.

While enabled and playing, each holds a clock `Division` that fires every
`bars` bars. The settings (`enabled`, `bars`, the ticked `choices`) survive
rebuilds and stops; the `Division` exists only from `run()` to `halt()`.

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
    from pyoscillate.patches.params import Param


@dataclass(frozen=True, eq=False)
class Evolve:
    """A rack's declaration of a starting evolution on a patch: change every
    `bars` bars, cycling through `choices` (phrases and progressions mixed are
    split by the dropdown each belongs to; empty keeps each patch's current
    choice only). A `Slot` turns it on for the patch it binds."""

    bars: int = 8
    choices: tuple[Any, ...] = ()


class Evolution:
    """One evolution timer of a patch and the choices it rotates through:
    those of `axis`, or none for the patch's own `on_evolve` hook."""

    DEFAULT_BARS: ClassVar[int] = 8
    MIN_BARS: ClassVar[int] = 1
    MAX_BARS: ClassVar[int] = 64

    def __init__(self, patch: Patch, axis: Param | None = None) -> None:
        self.patch = patch
        self.axis = axis
        self.enabled = False
        self.bars = self.DEFAULT_BARS
        # the choices ticked to take part, in the axis's own order; only the
        # starting one until a rack or listener ticks more
        self.choices: tuple[Any, ...] = (self.current,) if axis else ()
        self._clock: Clock | None = None
        self._division: Division | None = None
        self._fires = 0

    @property
    def running(self) -> bool:
        return self._division is not None

    @property
    def label(self) -> str:
        """What the listener calls this evolution: its dropdown's label, or
        "Evolve" for the patch's own hook."""
        return self.axis.spec.description if self.axis else "Evolve"

    @property
    def options(self) -> tuple[Any, ...]:
        """Everything the listener can tick, in the dropdown's order; empty
        for the patch's own hook."""
        if self.axis is None or self.axis.catalog is None:
            return ()
        return self.axis.catalog.members()

    @property
    def current(self) -> Any:
        """The choice the axis's dropdown is on now."""
        assert self.axis is not None and self.axis.catalog is not None
        return self.axis.catalog.by_index(int(self.axis.read(self.patch)))

    def order(self, chosen: tuple[Any, ...]) -> tuple[Any, ...]:
        """`chosen` in the dropdown's order, dropping what it doesn't offer."""
        return tuple(item for item in self.options if item in chosen)

    def declare(self, evolve: Evolve) -> None:
        """Adopt a rack's declared evolution and switch it on; only the
        `choices` this evolution's dropdown offers are taken."""
        self.enabled = True
        self.configure(evolve.bars)
        ticked = self.order(evolve.choices)
        if ticked:
            self.choices = ticked

    def configure(self, bars: float) -> None:
        """Set the interval in bars; a running timer retunes immediately."""
        self.bars = min(max(round(bars), self.MIN_BARS), self.MAX_BARS)
        if self._division is not None and self._clock is not None:
            self._division.steps = self._clock.bar * self.bars

    def set_choice(self, choice: Any, ticked: bool) -> None:
        """Tick or untick one choice, keeping the patch's own order."""
        chosen = {*self.choices, choice} if ticked else set(self.choices) - {choice}
        self.choices = self.order(tuple(chosen))

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
    def ticking(self) -> bool:
        """Whether the clock is moving through the interval: while the patch
        plays, evolving or holding, so a hold can still show where an
        evolution would land."""
        return self._clock is not None and self.patch.playing

    @property
    def progress(self) -> float:
        """How far through the current interval the clock is (0 just changed,
        approaching 1 as the next change nears); 0 when not ticking."""
        if not self.ticking:
            return 0.0
        assert self._clock is not None
        steps = self._clock.bar * self.bars
        return (self._clock.tick % steps) / steps

    @property
    def bars_left(self) -> float:
        """Bars until the next change; the full interval when not running."""
        return self.bars * (1 - self.progress)

    def rotation(self, count: int) -> tuple[Any, ...]:
        """The choice playing now followed by what `advance` will move to
        next, `count` in all, wrapping; just the one playing when fewer than
        two are ticked or the evolution is off. Empty for the patch's own
        hook, which has no choices."""
        if self.axis is None:
            return ()
        current = self.current
        if not self.enabled or len(self.choices) < 2:
            return (current,)
        position = self.choices.index(current) if current in self.choices else -1
        following = (
            self.choices[(position + step) % len(self.choices)]
            for step in range(1, count)
        )
        return (current, *following)

    def _fire(self) -> None:
        if self.axis is None:
            self.patch.on_evolve(self._fires)
        else:
            self.advance()
        self._fires += 1

    def advance(self) -> None:
        """Move the axis's dropdown to the next ticked choice after the one
        playing (the first when it isn't ticked), wrapping; a no-op with
        fewer than two ticked. The dropdown stays the single source, so a
        choice picked by hand continues from there."""
        if self.axis is None or len(self.choices) < 2:
            return
        current = self.current
        position = self.choices.index(current) if current in self.choices else -1
        self.axis.write(self.patch, self.choices[(position + 1) % len(self.choices)])
