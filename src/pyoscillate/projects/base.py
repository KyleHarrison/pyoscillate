"""Abstract project rack and its per-instance group ownership.

See docs/todos/oo-rack-refactor.md for the design discussion behind this.
"""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, ClassVar

from pyoscillate.clock import DEFAULT_TICKS_PER_BAR
from pyoscillate.controller import GroupController, GroupRuntime
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import Patch
from pyoscillate.patches.params import SliderSpec

if TYPE_CHECKING:
    from src.flet.base import EngineSpec


@dataclass(frozen=True)
class MacroControl:
    """One linear macro mapping for a patch parameter."""

    parameter: str
    start: float
    end: float

    def value(self, amount: float) -> float:
        return self.start + amount * (self.end - self.start)


@dataclass(frozen=True)
class MacroTarget:
    """One macro route from a declared group to its active patch.

    The group reference is the `GroupController` declaration itself, not a
    string name; `Rack` binds it to that declaration's fresh runtime group.
    """

    group: GroupController
    controls: tuple[MacroControl, ...]
    patch_names: frozenset[str] | None = None

    def apply(self, patch: Patch, amount: float) -> None:
        if self.patch_names is not None and patch.name not in self.patch_names:
            return
        for control in self.controls:
            value = control.value(amount)
            if control.parameter == "volume":
                patch.set(control.parameter, value)
            else:
                patch.configure(**{control.parameter: value})


@dataclass(frozen=True)
class MacroSpec:
    """One slider that controls a declarative collection of group targets."""

    slider: SliderSpec
    targets: tuple[MacroTarget, ...]

    def apply(self, rack: Rack, value: float) -> None:
        groups = {id(group_spec): group for group_spec, group in rack._group_bindings}
        for target in self.targets:
            patch = groups[id(target.group)].active_patch
            if patch is not None:
                target.apply(patch, value)


class Rack(ABC):
    """A project's patch groups plus the engine config to run them with.

    A subclass declares GroupController attributes; this class owns their
    fresh runtime GroupRuntime instances. Every EngineSpec field is explicit and
    none is derived by scanning patch capabilities.
    """

    bpm: float | None = None
    ticks_per_bar: int = DEFAULT_TICKS_PER_BAR
    needs_clock: bool = False
    harmony: ClassVar[Harmony | None] = None
    macro: MacroSpec | None = None
    nchnls: int = 2
    # `None` means "use flet.base's default"; a subclass overrides only if
    # it needs a different ceiling/starting level than every other project
    master_output_default: float | None = None
    master_output_max: float | None = None
    _group_bindings: tuple[tuple[GroupController, GroupRuntime], ...]
    _groups: tuple[GroupRuntime, ...]

    def __init__(self) -> None:
        harmony_spec = self.harmony
        self.harmony = (
            Harmony(
                key=harmony_spec.key,
                progression=harmony_spec.progression,
                bars_per_chord=harmony_spec.bars_per_chord,
            )
            if harmony_spec is not None
            else None
        )
        self._group_bindings = self._materialize_group_bindings()
        self._groups = tuple(group for _, group in self._group_bindings)
        for group in self._groups:
            setattr(self, group.name, group)

    def _materialize_group_bindings(self) -> tuple[tuple[GroupController, GroupRuntime], ...]:
        """Bind fresh runtime groups from declarations in inheritance order."""
        specs: list[GroupController] = []
        for cls in reversed(type(self).__mro__):
            for value in vars(cls).values():
                if isinstance(value, GroupController):
                    specs.append(value)
        if not specs:
            raise TypeError(f"{type(self).__name__} must declare GroupController attributes")
        return tuple((declaration, declaration.bind()) for declaration in specs)

    @property
    def groups(self) -> tuple[GroupRuntime, ...]:
        return self._groups

    def set_active_patch(self, patch: Patch, active: bool) -> None:
        """Track the live patch selected by the engine for rack operations."""
        for group in self.groups:
            if patch not in group.patches:
                continue
            group.active_patch = patch if active else None
            return


    def apply_macro(self, value: float) -> None:
        if self.macro is not None:
            self.macro.apply(self, value)

    @cached_property
    def group_controllers(self) -> tuple[GroupRuntime, ...]:
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
            macro=self.macro,
            group_controllers=self.group_controllers,
        )
