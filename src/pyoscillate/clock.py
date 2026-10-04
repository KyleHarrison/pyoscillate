from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import IntEnum

from pyo.lib.pattern import Pattern

from pyoscillate.tempo import Tempo

# default raw ticks per bar (a 128th note in 4/4) when a project's rack
# doesn't configure `Clock.ticks_per_bar` itself - see that field's docstring
DEFAULT_TICKS_PER_BAR = 128


class NoteDivision(IntEnum):
    """Standard bar-fraction divisions, as the divisor of a bar. Members are
    ordered slowest-to-fastest and each one doubles the previous, so a
    patch's rate control can move a fixed number of steps up or down this
    list to go slower or faster while always landing on a real musical
    subdivision - never an arbitrary raw tick count."""

    WHOLE = 1
    HALF = 2
    QUARTER = 4
    EIGHTH = 8
    SIXTEENTH = 16
    THIRTYSECOND = 32
    SIXTYFOURTH = 64
    ONE_TWENTY_EIGHTH = 128


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
    """Single master pulse, ticking once per `1/ticks_per_bar` of a bar,
    that every patch divides down from via `subscribe()` instead of running
    its own independent `Pattern`.

    A patch built with `Pattern(callback, time=tempo.eighth)` keeps its own
    private timer that starts counting from whenever `.play()` is called -
    so two such patches only share a tempo, not a phase, and rebuilding one
    mid-session (the normal edit-and-rerun-the-cell workflow) knocks it out
    of sync with the others. Routing every patch's trigger through one
    shared `Clock` instead means "every 2nd tick" always means the same
    ticks for everyone, so patches lock to a common downbeat and stay
    locked across rebuilds.

    `eq=False` keeps equality identity-based - see `Division`'s docstring.
    """

    tempo: Tempo
    # raw ticks per bar - the clock's timing resolution. Each project's rack
    # owns this, not a static value in this module: a higher number gives
    # patches a finer subdivision floor to tune down to (deep_house uses 128
    # so its per-patch step-count sliders can go well below a 16th note).
    ticks_per_bar: int = DEFAULT_TICKS_PER_BAR
    _tick: int = field(default=0, init=False, repr=False)
    _divisions: list[Division] = field(default_factory=list, init=False, repr=False)
    _pattern: Pattern = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._pattern = Pattern(self._advance, time=self._tick_seconds())

    def _tick_seconds(self) -> float:
        return self.tempo.bar / self.ticks_per_bar

    def retime(self) -> None:
        """Follow the tempo's current BPM. The tick count, and so every
        patch's position on the grid, is untouched - only the spacing of
        the ticks changes."""
        self._pattern.time = self._tick_seconds()

    def ticks(self, division: NoteDivision) -> int:
        """Raw ticks for a standard bar-fraction division, clamped to at
        least one tick (so a division finer than `ticks_per_bar` can express
        still fires every tick instead of raising or going silent)."""
        return max(1, self.ticks_per_bar // division)

    @staticmethod
    def rate_limits(base_division: NoteDivision) -> tuple[int, int]:
        """Inclusive slider offsets that remain valid `NoteDivision` values."""
        divisions = tuple(NoteDivision)
        base_index = divisions.index(base_division)
        return -base_index, len(divisions) - base_index - 1

    def ticks_for_rate(self, base_division: NoteDivision, rate: float) -> int:
        """Raw ticks for an offset from `base_division` in the rate slider."""
        divisions = tuple(NoteDivision)
        base_index = divisions.index(base_division)
        division_index = base_index + round(rate)
        if not 0 <= division_index < len(divisions):
            minimum, maximum = self.rate_limits(base_division)
            raise ValueError(
                f"rate must be between {minimum} and {maximum} for {base_division.name}"
            )
        return self.ticks(divisions[division_index])

    @property
    def tick(self) -> int:
        """Raw ticks elapsed since the clock was created. A patch that needs
        its own position within a division (e.g. which step of a bar a
        callback fired on) derives it from this - `clock.tick // steps` -
        rather than counting its own calls, so the answer is the same
        whenever the patch was built or restarted, matching `bar_index`."""
        return self._tick

    @property
    def bar(self) -> int:
        """Raw ticks in one bar - `ticks_per_bar` itself."""
        return self.ticks(NoteDivision.WHOLE)

    @property
    def bar_index(self) -> int:
        """Bars elapsed since the clock was created - the shared song
        position that rack-level state such as `Harmony` is counted in.
        Inside a `Division` callback this is the bar of the tick being
        fired."""
        return self._tick // self.bar

    @property
    def fourth(self) -> int:
        """Raw ticks in one quarter note."""
        return self.ticks(NoteDivision.QUARTER)

    @property
    def eighth(self) -> int:
        """Raw ticks in one 8th note."""
        return self.ticks(NoteDivision.EIGHTH)

    @property
    def sixteenth(self) -> int:
        """Raw ticks in one 16th note."""
        return self.ticks(NoteDivision.SIXTEENTH)

    @property
    def thirtysecond(self) -> int:
        """Raw ticks in one 32nd note."""
        return self.ticks(NoteDivision.THIRTYSECOND)

    def start(self) -> None:
        self._pattern.play()

    def stop(self) -> None:
        self._pattern.stop()

    def subscribe(self, steps: int, callback: Callable[[], None]) -> Division:
        """Return a Division that fires `callback` every `steps` raw ticks.

        Pass a value derived from this clock's own `sixteenth`/`eighth`/
        `fourth`/`bar` properties (or a multiple of one, e.g. `clock.bar * 8`)
        rather than a hardcoded number, so the same patch keeps its intended
        musical timing regardless of this clock's `ticks_per_bar`.

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
