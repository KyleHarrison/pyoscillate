from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from pyoscillate.clock import Clock, Division
from pyoscillate.patches.base import Patch


@dataclass(eq=False)
class GroupController:
    """Rack-level, infrequent (tens-of-bars) evolution: every `bars` bars,
    calls `Patch.on_evolve(index)` on whichever patch instance is currently
    active in each of `groups`.

    Unlike `Harmony`, this pushes rather than being pulled: it targets one
    specific active-patch instance per group, resolved by name at fire time
    via the `resolve` callback passed to `start()` - never bound to an
    instance at declare time, since round-robin group switching means the
    active instance can change between fires. `index` is this controller's
    own fire count, shared across every group it watches; a patch reads it
    as an index into its own musical data (e.g. `index % len(...)`).

    `eq=False` for the same reason as `Division`/`Clock`: it owns a
    `Division` and shouldn't be compared field-by-field.
    """

    groups: tuple[str, ...]
    bars: int
    _division: Division | None = field(default=None, init=False, repr=False)
    _index: int = field(default=0, init=False, repr=False)

    def start(self, clock: Clock, resolve: Callable[[str], Patch | None]) -> None:
        self._index = 0
        self._division = clock.subscribe(clock.bar * self.bars, lambda: self._fire(resolve))
        self._division.play()

    def stop(self) -> None:
        if self._division is not None:
            self._division.stop()
            self._division = None

    def _fire(self, resolve: Callable[[str], Patch | None]) -> None:
        for name in self.groups:
            patch = resolve(name)
            if patch is not None:
                patch.on_evolve(self._index)
        self._index += 1
