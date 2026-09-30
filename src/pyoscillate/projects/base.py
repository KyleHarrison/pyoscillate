"""Abstract project rack: engine config, patch `Slot`s, groups and macros
all declared as class attributes. `Rack.__init__` binds fresh runtime
instances of every declaration, so a rack needs no construction code.
"""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, replace
from typing import Any, ClassVar

from pyoscillate.clock import DEFAULT_TICKS_PER_BAR
from pyoscillate.controller import EvolvingRuntime, GroupController, GroupRuntime, Slot
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import Patch
from pyoscillate.patches.params import Param, SliderSpec


@dataclass(frozen=True)
class MacroControl:
    """One linear mapping of a macro amount (0-1 of its slider) onto a `Param`
    from `start` to `end`."""

    param: Param
    start: float
    end: float

    @classmethod
    def sweep(cls, param: Param) -> MacroControl:
        """The parameter's whole slider range."""
        return cls(param, param.spec.minimum, param.spec.maximum)

    def value(self, amount: float) -> float:
        return self.start + amount * (self.end - self.start)


@dataclass(frozen=True)
class MacroTarget:
    """One macro route: the controls to drive on one declared patch."""

    slot: Slot[Any]
    controls: tuple[MacroControl, ...]


@dataclass(frozen=True)
class Macro:
    """One rack-level slider that pushes a value across several patches - the
    manual, user-triggered counterpart to `Patch.on_evolve`'s clock-triggered
    push. Fully declarative: each target names a `Slot` and each control a
    `Param` object, and applying assigns the parameter on that rack's patch
    (staging it on every patch, live-updating the ones playing)."""

    slider: SliderSpec
    targets: tuple[MacroTarget, ...]

    def apply(self, rack: Rack, amount: float) -> None:
        for target in self.targets:
            patch = rack.patch_for(target.slot)
            for control in target.controls:
                control.param.write(patch, control.value(amount))


class Rack(ABC):
    """A project's patches and groups plus the engine config to run them.

    A subclass sets the class attributes below and declares
    `GroupController`/`EvolvingGroup`s of `Slot`s in its class body - groups in the order
    they are displayed, unless `layout` lists a different order (needed when a
    sidechain points at a group declared later in the display). The same
    object reads as its declaration on the class and as this rack's own
    runtime on an instance.
    """

    bpm: ClassVar[float]
    ticks_per_bar: ClassVar[int] = DEFAULT_TICKS_PER_BAR
    macros: ClassVar[tuple[Macro, ...]] = ()
    # group display order; empty means declaration order
    layout: ClassVar[tuple[GroupController, ...]] = ()
    nchnls: ClassVar[int] = 2
    # the master output's starting level and safety ceiling
    master_output_default: ClassVar[float] = 0.1
    master_output_max: ClassVar[float] = 0.2
    # the declared key and progression; every rack gets its own copy in
    # `__init__`, since the Flet key control mutates it
    harmony: Harmony = Harmony()

    def __init__(self) -> None:
        self.harmony = replace(self.harmony)
        declared: list[GroupController] = []
        for cls in reversed(type(self).__mro__):
            for value in vars(cls).values():
                if isinstance(value, GroupController):
                    declared.append(value)
        if not declared:
            raise TypeError(
                f"{type(self).__name__} must declare GroupController attributes"
            )
        slots = [slot for group in declared for slot in group.slots]
        self._patches: dict[Slot[Any], Patch] = {slot: slot.bind() for slot in slots}
        self._groups: dict[GroupController, GroupRuntime] = {
            group: group.bind(tuple(self._patches[slot] for slot in group.slots))
            for group in declared
        }
        for slot in slots:
            slot.link(self._patches[slot], self._groups)
        self.groups = tuple(self._groups[group] for group in (self.layout or declared))
        self.evolving_groups = tuple(
            g for g in self.groups if isinstance(g, EvolvingRuntime)
        )

    def patch_for(self, slot: Slot[Any]) -> Patch:
        """This rack's bound patch for `slot`."""
        return self._patches[slot]

    def group_for(self, group: GroupController) -> GroupRuntime:
        """This rack's bound runtime for `group`."""
        return self._groups[group]
