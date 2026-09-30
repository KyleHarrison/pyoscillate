"""Class-level declarations for a rack - patches (`Slot`), groups
(`GroupController`, `EvolvingGroup`), sidechains - and the per-rack runtime
objects they bind to.

A declaration is an immutable descriptor on a `Rack` subclass. Read on the
class it is the declaration itself (so a `Macro` or a `SidechainSource` can
point at it); read on a rack instance it is that rack's own fresh runtime
object (`rack.pad_wash` is the `SoundscapeWash`, `rack.kick` the group), so
no rack shares mutable state and nothing is looked up by name.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, overload

from pyoscillate.clock import Clock, Division
from pyoscillate.patches.base import Patch, Sidechain

if TYPE_CHECKING:
    from pyoscillate.projects.base import Rack


@dataclass(frozen=True, eq=False)
class SidechainSource:
    """Declares that a patch ducks off a rack group: `group` is the group's
    own declaration (defined earlier in the rack's class body)."""

    group: GroupController
    depth: float = 0.6
    release: float = 0.15


class Slot[P: Patch]:
    """Declares one patch in a rack: its class, starting `Param` values, and
    sidechains. `Rack` binds a fresh instance per rack; on a rack instance the
    slot reads as that instance, typed as `patch_class`."""

    def __init__(
        self,
        patch_class: type[P],
        *,
        sidechains: tuple[SidechainSource, ...] = (),
        **values: float,
    ) -> None:
        self.patch_class = patch_class
        self.sidechains = sidechains
        self.values = values

    def bind(self) -> P:
        return self.patch_class(**self.values)

    def link(self, patch: P, groups: dict[GroupController, GroupRuntime]) -> None:
        """Point `patch` at this rack's runtime groups for each sidechain."""
        patch.sidechains = tuple(
            Sidechain(groups[source.group], source.depth, source.release)
            for source in self.sidechains
        )

    @overload
    def __get__(self, obj: None, owner: type[Any]) -> Slot[P]: ...
    @overload
    def __get__(self, obj: Rack, owner: type[Any]) -> P: ...
    def __get__(self, obj: Rack | None, owner: type[Any]) -> Slot[P] | P:
        if obj is None:
            return self
        return obj.patch_for(self)


@dataclass(frozen=True, eq=False)
class GroupController:
    """Declares a titled group of patch alternatives shown together in one
    Flet panel. `slots` are the patches' `Slot` declarations; on a rack
    instance the attribute reads as the bound `GroupRuntime`."""

    title: str
    slots: tuple[Slot[Any], ...]
    summary: str = ""

    def bind(self, patches: tuple[Patch, ...]) -> GroupRuntime:
        return GroupRuntime(self.title, patches, self.summary)

    @overload
    def __get__(self, obj: None, owner: type[Any]) -> GroupController: ...
    @overload
    def __get__(self, obj: Rack, owner: type[Any]) -> GroupRuntime: ...
    def __get__(
        self, obj: Rack | None, owner: type[Any]
    ) -> GroupController | GroupRuntime:
        if obj is None:
            return self
        return obj.group_for(self)


@dataclass(frozen=True, eq=False)
class EvolvingGroup(GroupController):
    """A group that also owns a rack-level, infrequent (tens-of-bars)
    evolution timer: every `bars` bars it calls `Patch.on_evolve(index)` on
    each patch playing in the group (see `EvolvingRuntime`)."""

    bars: int = 1
    repeat: int = 1

    def bind(self, patches: tuple[Patch, ...]) -> EvolvingRuntime:
        return EvolvingRuntime(
            self.title, patches, self.summary, self.bars, self.repeat
        )


@dataclass(eq=False)
class GroupRuntime:
    """One rack's group: its bound patches."""

    title: str
    patches: tuple[Patch, ...]
    summary: str = ""

    def playing_patches(self) -> tuple[Patch, ...]:
        """The patches in this group that are currently playing."""
        return tuple(patch for patch in self.patches if patch.playing)


@dataclass(eq=False)
class EvolvingRuntime(GroupRuntime):
    """A group's evolution timer. `index` passed to `on_evolve` is the fire
    count divided by `repeat` (so each index holds for `repeat` fires before
    advancing); a patch reads it as an index into its own musical data (e.g.
    `index % len(...)`).

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
