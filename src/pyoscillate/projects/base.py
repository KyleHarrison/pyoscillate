"""Abstract project rack: the shared shape every project's `rack.py`
implements - engine config as class attributes, and the patches and groups
built once in `build_groups()` and held as typed attributes on the rack.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import ClassVar

from pyoscillate.clock import DEFAULT_TICKS_PER_BAR
from pyoscillate.controller import EvolvingGroup, GroupController
from pyoscillate.harmony import Harmony
from pyoscillate.patches.params import SliderSpec


@dataclass(frozen=True)
class Macro:
    """One rack-level slider that pushes a value across several patches - the
    manual, user-triggered counterpart to `Patch.on_evolve`'s clock-triggered
    push.

    `apply` is a method of the rack subclass, called as `apply(rack, value)`;
    it assigns parameters directly on the rack's own typed patch attributes
    (`self.pad.chorus_depth = ...`). Assigning stages the value on every
    patch, and live-updates the ones playing, so it needs no lookup of "which
    patch is active" and no branching on the active style.
    """

    slider: SliderSpec
    apply: Callable[[Rack, float], None]


class Rack(ABC):
    """A project's patch groups plus the engine config to run them with.

    A subclass sets the class attributes below as needed and implements
    `build_groups()`, which constructs every patch, stores the ones a macro
    or sidechain needs as typed attributes on `self`, and returns the
    `GroupController`s in display order. Everything else is concrete and
    shared.
    """

    bpm: ClassVar[float]
    ticks_per_bar: ClassVar[int] = DEFAULT_TICKS_PER_BAR
    harmony: ClassVar[Harmony] = Harmony()
    macros: ClassVar[tuple[Macro, ...]] = ()
    nchnls: ClassVar[int] = 2
    # the master output's starting level and safety ceiling
    master_output_default: ClassVar[float] = 0.1
    master_output_max: ClassVar[float] = 0.2

    def __init__(self) -> None:
        self.groups = self.build_groups()
        self.evolving_groups = tuple(
            g for g in self.groups if isinstance(g, EvolvingGroup)
        )

    @abstractmethod
    def build_groups(self) -> tuple[GroupController, ...]:
        """Construct every patch instance and its `GroupController` grouping."""
