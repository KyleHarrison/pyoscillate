from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from pyoscillate.clock import Clock, Division
from pyoscillate.patches.base import Patch


@dataclass(frozen=True)
class GroupController:
    """Immutable class-level declaration for one rack group."""

    name: str
    title: str
    patches: tuple[Callable[[], Patch], ...]
    summary: str = ""
    bars: int | None = None
    repeat: int = 1

    def bind(self) -> GroupRuntime:
        return GroupRuntime(
            self.name,
            self.title,
            tuple(factory() for factory in self.patches),
            self.summary,
            self.bars,
            self.repeat,
        )


@dataclass(eq=False)
class GroupRuntime:
    """Per-rack group state for patches, selection, and evolution timing."""

    name: str
    title: str
    patches: tuple[Patch, ...]
    summary: str = ""
    bars: int | None = None
    repeat: int = 1
    active_patch: Patch | None = field(default=None, init=False, repr=False)
    _division: Division | None = field(default=None, init=False, repr=False)
    _fire_count: int = field(default=0, init=False, repr=False)
    _clock: Clock | None = field(default=None, init=False, repr=False)

    def start(self, clock: Clock) -> None:
        assert self.bars is not None
        self._fire_count = 0
        self._clock = clock
        self._subscribe()

    def stop(self) -> None:
        if self._division is not None:
            self._division.stop()
            self._division = None
        self._clock = None

    def set_bars(self, bars: int) -> None:
        self.bars = max(1, bars)
        if self._clock is not None:
            self._subscribe()

    def set_repeat(self, repeat: int) -> None:
        self.repeat = max(1, repeat)

    def _subscribe(self) -> None:
        assert self._clock is not None
        assert self.bars is not None
        if self._division is not None:
            self._division.stop()
        self._division = self._clock.subscribe(self._clock.bar * self.bars, self._fire)
        self._division.play()

    def _fire(self) -> None:
        index = self._fire_count // self.repeat
        patch = self.active_patch
        if patch is not None:
            patch.on_evolve(index)
        self._fire_count += 1
