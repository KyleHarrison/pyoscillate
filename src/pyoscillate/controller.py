from __future__ import annotations

from dataclasses import dataclass, field

from pyoscillate.clock import Clock, Division
from pyoscillate.patches.base import Patch


@dataclass(eq=False)
class GroupController:
    """A titled group of patch alternatives presented together in one Flet
    panel. Racks hold the group object itself (`self.kick`), and a
    `SidechainSource` points at it directly, so nothing refers to a group by
    name.

    `eq=False` so two groups never compare field-by-field.
    """

    title: str
    patches: tuple[Patch, ...]
    summary: str = ""

    def playing_patches(self) -> tuple[Patch, ...]:
        """The patches in this group that are currently playing."""
        return tuple(patch for patch in self.patches if patch.playing)


@dataclass(eq=False)
class EvolvingGroup(GroupController):
    """A `GroupController` with a rack-level, infrequent (tens-of-bars)
    evolution timer: every `bars` bars it calls `Patch.on_evolve(index)` on
    each patch currently playing in the group. `index` is the group's own
    fire count divided by `repeat` (so each index holds for `repeat` fires
    before advancing); a patch reads it as an index into its own musical data
    (e.g. `index % len(...)`).

    `bars` and `repeat` are live-adjustable via `set_bars()`/`set_repeat()`
    (a rack's Flet UI wires a slider to each) - `set_bars` re-subscribes the
    running `Division` at the new interval, `set_repeat` just changes how the
    fire count is divided.
    """

    bars: int = 1
    repeat: int = 1
    _running: bool = field(default=False, init=False, repr=False)
    _fire_count: int = field(default=0, init=False, repr=False)
    _clock: Clock = field(init=False, repr=False)
    _division: Division = field(init=False, repr=False)

    def start(self, clock: Clock) -> None:
        self._fire_count = 0
        self._clock = clock
        self._running = True
        self._subscribe()

    def stop(self) -> None:
        if self._running:
            self._division.stop()
            self._running = False

    def set_bars(self, bars: int) -> None:
        self.bars = max(1, bars)
        if self._running:
            self._division.stop()
            self._subscribe()

    def set_repeat(self, repeat: int) -> None:
        self.repeat = max(1, repeat)

    def _subscribe(self) -> None:
        self._division = self._clock.subscribe(self._clock.bar * self.bars, self._fire)
        self._division.play()

    def _fire(self) -> None:
        index = self._fire_count // self.repeat
        for patch in self.playing_patches():
            patch.on_evolve(index)
        self._fire_count += 1
