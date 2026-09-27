"""Abstract project rack: the shared shape every project's `rack.py`
implements instead of a module-level `PATCHES`/`GROUP_TITLES`/`PATCH_GROUPS`
trio plus loose `BPM`/`TICKS_PER_BAR`/`HARMONY`/`GROUP_CONTROLLERS` globals.

See docs/todos/oo-rack-refactor.md for the design discussion behind this.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from functools import cached_property
from typing import TYPE_CHECKING

from pyoscillate.clock import DEFAULT_TICKS_PER_BAR
from pyoscillate.controller import GroupController
from pyoscillate.harmony import Harmony

if TYPE_CHECKING:
    from src.flet.base import EngineSpec


class Rack(ABC):
    """A project's patch groups plus the engine config to run them with.

    A subclass sets the class attributes below as needed and implements
    `build_groups()`; everything else (`groups`, `group_controllers`,
    `engine_spec()`) is concrete and shared. Every `EngineSpec` field is an
    explicit attribute here - none of it is derived by scanning
    `build_groups()`'s patches for `needs_clock`/`needs_tempo` flags (see the
    "Open questions" note in docs/todos/oo-rack-refactor.md on why that's
    deliberate).
    """

    bpm: float | None = None
    ticks_per_bar: int = DEFAULT_TICKS_PER_BAR
    needs_clock: bool = False
    harmony: Harmony | None = None
    nchnls: int = 2
    # `None` means "use flet.base's default"; a subclass overrides only if
    # it needs a different ceiling/starting level than every other project
    master_output_default: float | None = None
    master_output_max: float | None = None

    @abstractmethod
    def build_groups(self) -> tuple[GroupController, ...]:
        """Construct every patch instance and its `GroupController` grouping."""

    @cached_property
    def groups(self) -> tuple[GroupController, ...]:
        return self.build_groups()

    @cached_property
    def group_controllers(self) -> tuple[GroupController, ...]:
        """The subset of `groups` that own a rack-level evolution timer
        (`bars is not None`) - derived from `groups` rather than declared
        separately, so a group's evolution timer is declared in exactly one
        place instead of being listed twice."""
        return tuple(group for group in self.groups if group.bars is not None)

    def engine_spec(self) -> EngineSpec:
        from src.flet.base import MASTER_OUTPUT_DEFAULT, MASTER_OUTPUT_MAX, EngineSpec

        return EngineSpec(
            nchnls=self.nchnls,
            bpm=self.bpm,
            needs_clock=self.needs_clock,
            ticks_per_bar=self.ticks_per_bar,
            master_output_default=self.master_output_default
            if self.master_output_default is not None
            else MASTER_OUTPUT_DEFAULT,
            master_output_max=self.master_output_max
            if self.master_output_max is not None
            else MASTER_OUTPUT_MAX,
            harmony=self.harmony,
            group_controllers=self.group_controllers,
        )
