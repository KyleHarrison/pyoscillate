"""Class-level declarations for a rack - patches (`Slot`), groups
(`GroupController`, `EvolvingGroup`) with their slider controls
(`GroupControl`), sidechains - and the per-rack runtime objects they bind to.

A declaration is an immutable descriptor on a `Rack` subclass. Read on the
class it is the declaration itself (so a `GroupControl` or a `SidechainSource`
can point at it); read on a rack instance it is that rack's own fresh runtime
object (`rack.pad_wash` is the `SoundscapeWash`, `rack.kick` the group), so
no rack shares mutable state and nothing is looked up by name.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, overload

from pyoscillate.clock import Clock, Division
from pyoscillate.patches.base import Patch, Sidechain
from pyoscillate.patches.params import Param, SliderSpec
from pyoscillate.patches.sweep import ParamSweep

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
    sidechains, and any `sweeps` that start enabled. `Rack` binds a fresh
    instance per rack; on a rack instance the slot reads as that instance,
    typed as `patch_class`."""

    def __init__(
        self,
        patch_class: type[P],
        *,
        sidechains: tuple[SidechainSource, ...] = (),
        sweeps: tuple[ParamSweep, ...] = (),
        **values: float,
    ) -> None:
        self.patch_class = patch_class
        self.sidechains = sidechains
        self.sweeps = sweeps
        self.values = values

    def bind(self) -> P:
        patch = self.patch_class(**self.values)
        patch.declare_sweeps(self.sweeps)
        return patch

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
class ParamControl:
    """One linear mapping of a control amount (0-1 of its slider) onto a
    `Param` from `start` to `end`."""

    param: Param
    start: float
    end: float

    @classmethod
    def sweep(cls, param: Param) -> ParamControl:
        """The parameter's whole slider range."""
        return cls(param, param.spec.minimum, param.spec.maximum)

    def value(self, amount: float) -> float:
        return self.start + amount * (self.end - self.start)


@dataclass(frozen=True, eq=False)
class SlotTarget:
    """One control route: `Param` mappings driven on one declared patch, which
    must be a slot somewhere inside the group that owns the control."""

    slot: Slot[Any]
    controls: tuple[ParamControl, ...]

    def apply(self, group: GroupRuntime, amount: float) -> None:
        patch = group.patch_for(self.slot)
        for control in self.controls:
            control.param.write(patch, control.value(amount))


@dataclass(frozen=True, eq=False)
class FanOut:
    """One control route onto every patch inside the group that has the named
    `Param` (recognised across style overrides, see `Param.origin`); patches
    without it are skipped."""

    controls: tuple[ParamControl, ...]

    def apply(self, group: GroupRuntime, amount: float) -> None:
        for patch in group.patches:
            for control in self.controls:
                for own in patch.params:
                    if own.origin is control.param.origin:
                        own.write(patch, control.value(amount))


@dataclass(frozen=True, eq=False)
class GroupControl:
    """One slider on a group that pushes a value across its patches - the
    manual, user-triggered counterpart to `Patch.on_evolve`'s clock-triggered
    push. Fully declarative: each target is a `SlotTarget` (exact patch), a
    `FanOut` (every patch with a `Param`) or another `GroupControl` declared on
    an inner group, which receives the same amount - so an outer control can
    move inner ones while each inner group keeps its own per-patch mapping."""

    slider: SliderSpec
    targets: tuple[SlotTarget | FanOut | GroupControl, ...]


@dataclass(frozen=True, eq=False)
class GroupController:
    """Declares a titled group shown together in one Flet panel. `members` are
    `Slot`s (patch alternatives) and inner `GroupController`s, so groups nest;
    `controls` are the group's own sliders. On a rack instance the attribute
    reads as the bound `GroupRuntime`."""

    title: str
    members: tuple[Slot[Any] | GroupController, ...]
    summary: str = ""
    controls: tuple[GroupControl, ...] = ()

    def __post_init__(self) -> None:
        slots = set(self.slots)
        inner = {c for group in self.descendants() for c in group.controls}
        for control in self.controls:
            for target in control.targets:
                if isinstance(target, SlotTarget) and target.slot not in slots:
                    raise ValueError(
                        f"{self.title}: control '{control.slider.name}' targets a "
                        "slot outside the group"
                    )
                if isinstance(target, GroupControl) and target not in inner:
                    raise ValueError(
                        f"{self.title}: control '{control.slider.name}' targets a "
                        "control that no inner group declares"
                    )

    @property
    def own_slots(self) -> tuple[Slot[Any], ...]:
        """The slots listed directly in this group."""
        return tuple(m for m in self.members if isinstance(m, Slot))

    @property
    def children(self) -> tuple[GroupController, ...]:
        """The groups listed directly in this group."""
        return tuple(m for m in self.members if isinstance(m, GroupController))

    def descendants(self) -> tuple[GroupController, ...]:
        """Every group nested inside this one, depth-first."""
        return tuple(
            nested
            for child in self.children
            for nested in (child, *child.descendants())
        )

    @property
    def slots(self) -> tuple[Slot[Any], ...]:
        """Every slot in this group, nested groups included."""
        return (
            *self.own_slots,
            *(slot for child in self.children for slot in child.slots),
        )

    def bind(
        self,
        patches: dict[Slot[Any], Patch],
        runtimes: dict[GroupController, GroupRuntime],
    ) -> GroupRuntime:
        """This group's runtime, binding inner groups first; `runtimes`
        collects every group bound so far."""
        if self in runtimes:
            return runtimes[self]
        children = tuple(child.bind(patches, runtimes) for child in self.children)
        runtime = self._runtime(patches, children)
        runtimes[self] = runtime
        return runtime

    def _runtime(
        self, patches: dict[Slot[Any], Patch], children: tuple[GroupRuntime, ...]
    ) -> GroupRuntime:
        return GroupRuntime(
            self.title,
            tuple(patches[slot] for slot in self.slots),
            self.summary,
            children=children,
            controls=self.controls,
            slot_patches={slot: patches[slot] for slot in self.slots},
            own_patches=tuple(patches[slot] for slot in self.own_slots),
        )

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

    def _runtime(
        self, patches: dict[Slot[Any], Patch], children: tuple[GroupRuntime, ...]
    ) -> EvolvingRuntime:
        return EvolvingRuntime(
            self.title,
            tuple(patches[slot] for slot in self.slots),
            self.summary,
            children=children,
            controls=self.controls,
            slot_patches={slot: patches[slot] for slot in self.slots},
            own_patches=tuple(patches[slot] for slot in self.own_slots),
            bars=self.bars,
            repeat=self.repeat,
        )


@dataclass(eq=False)
class GroupRuntime:
    """One rack's group: its bound patches (nested groups' included), inner
    `children` runtimes, and the current amount of each `GroupControl`."""

    title: str
    patches: tuple[Patch, ...]
    summary: str = ""
    children: tuple[GroupRuntime, ...] = ()
    controls: tuple[GroupControl, ...] = ()
    slot_patches: dict[Slot[Any], Patch] = field(default_factory=dict)
    own_patches: tuple[Patch, ...] = ()
    values: dict[GroupControl, float] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.values = {control: control.slider.default for control in self.controls}

    def playing_patches(self) -> tuple[Patch, ...]:
        """The patches in this group that are currently playing."""
        return tuple(patch for patch in self.patches if patch.playing)

    def patch_for(self, slot: Slot[Any]) -> Patch:
        """This group's bound patch for `slot`."""
        return self.slot_patches[slot]

    def walk(self) -> tuple[GroupRuntime, ...]:
        """This group then every group nested inside it, depth-first."""
        return (self, *(nested for child in self.children for nested in child.walk()))

    def apply(self, control: GroupControl, amount: float) -> None:
        """Move `control` (declared on this group) to `amount`, assigning its
        `Param`s and moving any inner control it targets."""
        self.values[control] = amount
        for target in control.targets:
            if isinstance(target, GroupControl):
                self._owner_of(target).apply(target, amount)
            else:
                target.apply(self, amount)

    def _owner_of(self, control: GroupControl) -> GroupRuntime:
        for group in self.walk():
            if control in group.controls:
                return group
        raise LookupError(f"{self.title}: no inner group owns that control")


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
