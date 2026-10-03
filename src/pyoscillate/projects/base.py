"""Abstract project rack: engine config, patch `Slot`s and groups (with their
controls) all declared as class attributes. `Rack.__init__` binds fresh runtime
instances of every declaration, so a rack needs no construction code.
"""

from __future__ import annotations

from abc import ABC
from dataclasses import replace
from typing import Any, ClassVar

from pyoscillate.clock import DEFAULT_TICKS_PER_BAR
from pyoscillate.controller import EvolvingRuntime, GroupController, GroupRuntime, Slot
from pyoscillate.patches.base import Patch
from pyoscillate.theory.harmony import Harmony


class Rack(ABC):
    """A project's patches and groups plus the engine config to run them.

    A subclass sets the class attributes below and declares
    `GroupController`/`EvolvingGroup`s of `Slot`s (and of inner groups, which
    nest in the display) in its class body - top-level groups in the order
    they are declared, unless `layout` lists a different order (needed when a
    sidechain points at a group declared later in the display). The same
    object reads as its declaration on the class and as this rack's own
    runtime on an instance.
    """

    bpm: ClassVar[float]
    ticks_per_bar: ClassVar[int] = DEFAULT_TICKS_PER_BAR
    # top-level group display order; empty means declaration order, with every
    # group nested inside another left out
    layout: ClassVar[tuple[GroupController, ...]] = ()
    nchnls: ClassVar[int] = 2
    # the master output's starting level and safety ceiling
    master_output_default: ClassVar[float] = 0.8
    master_output_max: ClassVar[float] = 1.0
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
        slots = list(dict.fromkeys(slot for group in declared for slot in group.slots))
        self._patches: dict[Slot[Any], Patch] = {slot: slot.bind() for slot in slots}
        self._groups: dict[GroupController, GroupRuntime] = {}
        for group in declared:
            group.bind(self._patches, self._groups)
        for slot in slots:
            slot.link(self._patches[slot], self._groups)
        nested = {inner for group in declared for inner in group.descendants()}
        top_level = self.layout or tuple(g for g in declared if g not in nested)
        self.groups = tuple(self._groups[group] for group in top_level)
        self.evolving_groups = tuple(
            nested_group
            for group in self.groups
            for nested_group in group.walk()
            if isinstance(nested_group, EvolvingRuntime)
        )

    def patch_for(self, slot: Slot[Any]) -> Patch:
        """This rack's bound patch for `slot`."""
        return self._patches[slot]

    def group_for(self, group: GroupController) -> GroupRuntime:
        """This rack's bound runtime for `group`."""
        return self._groups[group]
