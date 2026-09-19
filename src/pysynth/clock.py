from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import ClassVar

from pyo.lib.pattern import Pattern

from pysynth.tempo import Tempo

# step counts, in 16th notes, for each named subdivision - pass these (or a
# multiple, e.g. `BAR * 8`) to `Clock.subscribe()`
SIXTEENTH = 1
EIGHTH = 2
FOURTH = 4
BAR = 16


@dataclass(eq=False)
class Division:
    """One patch's slice of a `Clock`: fires `callback` every `steps` master
    ticks. Rebuilding the owning patch and resubscribing lands back on the
    grid at whatever tick the clock is currently on, rather than resetting
    phase to zero - so two patches with the same `steps` always fire on the
    same tick, however long after each other they were started.

    `eq=False` keeps equality/hashing identity-based (the default `object`
    behaviour) - `Division` and `Clock` reference each other, so the
    generated field-by-field `__eq__` would recurse into each other's field
    tuples.
    """

    clock: Clock
    steps: int
    callback: Callable[[], None]

    def play(self) -> None:
        self.clock._register(self)

    def stop(self) -> None:
        self.clock._unregister(self)


@dataclass(eq=False)
class Clock:
    """Single master pulse, ticking once per 16th note, that every patch
    divides down from via `subscribe()` instead of running its own
    independent `Pattern`.

    A patch built with `Pattern(callback, time=tempo.eighth)` keeps its own
    private timer that starts counting from whenever `.play()` is called -
    so two such patches only share a tempo, not a phase, and rebuilding one
    mid-session (the normal edit-and-rerun-the-cell workflow) knocks it out
    of sync with the others. Routing every patch's trigger through one
    shared `Clock` instead means "every 2nd tick" always means the same
    ticks for everyone, so patches lock to a common downbeat and stay
    locked across rebuilds.

    `eq=False` keeps equality identity-based - see `Division`'s docstring -
    and also matters for `PatchRack.toggle()`, which compares previous
    `build()` arguments (including this `clock`) with `==` to decide
    whether to treat a rerun as an off/on toggle.
    """

    SIXTEENTH: ClassVar[int] = SIXTEENTH
    EIGHTH: ClassVar[int] = EIGHTH
    FOURTH: ClassVar[int] = FOURTH
    BAR: ClassVar[int] = BAR

    tempo: Tempo
    _tick: int = field(default=0, init=False, repr=False)
    _divisions: list[Division] = field(default_factory=list, init=False, repr=False)
    _pattern: Pattern = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._pattern = Pattern(self._advance, time=self.tempo.sixteenth)

    def start(self) -> None:
        self._pattern.play()

    def stop(self) -> None:
        self._pattern.stop()

    def subscribe(self, steps: int, callback: Callable[[], None]) -> Division:
        """Return a Division that fires `callback` every `steps` 16th notes.

        Not yet listening - call `.play()` on the result (as `Patch.start()`
        does) to join the grid, and `.stop()` to leave it.
        """
        return Division(clock=self, steps=steps, callback=callback)

    def _register(self, division: Division) -> None:
        if division not in self._divisions:
            self._divisions.append(division)

    def _unregister(self, division: Division) -> None:
        if division in self._divisions:
            self._divisions.remove(division)

    def _advance(self) -> None:
        for division in list(self._divisions):
            if self._tick % division.steps == 0:
                division.callback()
        self._tick += 1
