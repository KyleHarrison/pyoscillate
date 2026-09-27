from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from pyoscillate.clock import Clock, Division
from pyoscillate.patches.base import Patch


@dataclass(eq=False)
class GroupController:
    """A named group of patch alternatives presented together in one Flet
    panel (`name`/`title`/`patches`/`summary` - what a separate
    `PatchGroupDef` used to hold), plus - when `bars` is set - the
    rack-level, infrequent (tens-of-bars) evolution timer for that same
    group: every `bars` bars, calls `Patch.on_evolve(index)` on whichever
    patch instance is currently active in this group.

    These two concerns were split across two objects that a rack had to
    keep in sync by hand (a `PatchGroupDef` and a separately-constructed
    `GroupController` referenced from both `PatchGroupDef.controller` and
    `Rack.group_controllers`). Folding them into one means a group's name,
    its patches, and its own evolution timer are declared in exactly one
    place; `Rack.group_controllers` is derived from `Rack.groups` by
    filtering for `bars is not None` rather than duplicated.

    Unlike `Harmony`, the evolution timer pushes rather than being pulled:
    it targets this group's currently active patch, resolved by name at
    fire time via the `resolve` callback passed to `start()` - never bound
    to an instance at declare time, since round-robin group switching means
    the active instance can change between fires. `index` passed to
    `on_evolve` is this controller's own fire count divided by `repeat` (so
    each index holds for `repeat` fires before advancing); a patch reads it
    as an index into its own musical data (e.g. `index % len(...)`).

    `bars` and `repeat` are live-adjustable via `set_bars()`/`set_repeat()`
    (a rack's Flet UI wires a slider to each, when `bars is not None`) -
    `set_bars` re-subscribes the running `Division` at the new interval,
    `set_repeat` just changes how the fire count is divided.

    `eq=False` for the same reason as `Division`/`Clock`: it owns a
    `Division` and shouldn't be compared field-by-field.
    """

    name: str
    title: str
    patches: tuple[Patch, ...]
    summary: str = ""
    # `None` means this group has no rack-level evolution timer, just the
    # patch grouping/UI.
    bars: int | None = None
    repeat: int = 1
    _division: Division | None = field(default=None, init=False, repr=False)
    _fire_count: int = field(default=0, init=False, repr=False)
    _clock: Clock | None = field(default=None, init=False, repr=False)
    _resolve: Callable[[str], Patch | None] | None = field(default=None, init=False, repr=False)

    def start(self, clock: Clock, resolve: Callable[[str], Patch | None]) -> None:
        assert self.bars is not None
        self._fire_count = 0
        self._clock = clock
        self._resolve = resolve
        self._subscribe()

    def stop(self) -> None:
        if self._division is not None:
            self._division.stop()
            self._division = None
        self._clock = None
        self._resolve = None

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
        patch = self._resolve(self.name) if self._resolve is not None else None
        if patch is not None:
            patch.on_evolve(index)
        self._fire_count += 1
