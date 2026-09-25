"""Shared trigger/envelope/scheduling plumbing for the drums archetype.

Every gated drum voice (kick, snare, clap, hat, ...) follows the same shape:
one `Trig()` fires per hit, one or more `TrigEnv`s read a break-point table
off it, and a `Clock` `Division` schedules the hit with a live `rate`
control. `DrumVoice` factors that shape out so a concrete voice's `build()`
only has to describe what's unique to it.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, ClassVar

from pyo import PyoObject
from pyo.lib.tables import ExpTable
from pyo.lib.triggers import Trig, TrigEnv

from pyoscillate.clock import Clock, Division, NoteDivision
from pyoscillate.patches.base import Patch


def semitone_ratio(semitones: float) -> float:
    """Frequency ratio for a pitch shift of `semitones`, for detuning an
    oscillator relative to a body/root frequency."""
    return 2 ** (semitones / 12)


class DrumVoice(Patch):
    """Base for a gated drums-archetype voice. Concrete voices call
    `self.envelope(...)` instead of hand-pairing `ExpTable`/`TrigEnv`, and
    `self.schedule(...)` instead of hand-wiring `clock.subscribe` and a
    `rate` control - both auto-register their Pyo objects for `resources`,
    so a `build()` can't forget to retain one (the crash risk
    `patches/CLAUDE.md`'s resource-ownership rule exists to prevent).
    """

    needs_tempo: ClassVar[bool] = True
    needs_clock: ClassVar[bool] = True

    def _reset(self) -> None:
        """Call at the top of `build()`: fresh Pyo objects and a fresh
        resources/controls list every call, since one voice instance's
        `build()` may run again on a rebuild."""
        super()._reset()
        self.trigger = Trig()
        self.retain(self.trigger)
        self._division: Division | None = None

    def envelope(
        self,
        points: list[tuple[int, float]],
        *,
        dur: float,
        mul: float = 1.0,
        add: float = 0.0,
        exp: float = 1.0,
    ) -> TrigEnv:
        """A `TrigEnv` reading an `ExpTable` off this voice's trigger; the
        table and envelope are auto-retained."""
        table = ExpTable(points, exp=exp)
        env = TrigEnv(self.trigger, table, dur=dur, mul=mul, add=add)
        self.retain(table, env)
        return env

    def schedule(
        self,
        base_division: NoteDivision,
        rate: float,
        clock: Clock,
        callback: Callable[[], None],
    ) -> Division:
        """Subscribe `callback` on `clock` and pre-register the `rate` live
        control, so `build()` never has to hand-wire it."""
        division = clock.subscribe(clock.ticks_for_rate(base_division, rate), callback)
        self.controls["rate"] = lambda value: setattr(
            division, "steps", clock.ticks_for_rate(base_division, value)
        )
        self._division = division
        return division

    def step_pattern(
        self, cycle: int, pattern: dict[int, Any] | set[int]
    ) -> Callable[[], tuple[int, Any | None]]:
        """Zero-arg callable for a `schedule()` callback: each call advances
        an internal step counter (mod `cycle`) and returns `(step, value)`,
        where `value` is `pattern[step]` for a dict, `True`/`None` for a
        set. The concrete voice's own callback wraps this to decide what a
        hit does (trigger, reset, accent, recompute pitch, ...)."""
        counter = {"step": 0}

        def check() -> tuple[int, Any | None]:
            step = counter["step"] % cycle
            value = pattern.get(step) if isinstance(pattern, dict) else (True if step in pattern else None)
            counter["step"] += 1
            return step, value

        return check

    def finish(self, voice: PyoObject, controls: dict[str, Callable[[Any], None]]) -> Patch:
        """Wire this voice's `sequencer`/`voice`/`controls` from everything
        `envelope()`/`schedule()`/`retain()` accumulated plus this build's
        own `voice`/`controls`, and return `self` now that it's built."""
        if self._division is None:
            raise RuntimeError(f"{type(self).__name__}.build() never called self.schedule(...)")
        self.sequencer = self._division
        self.voice = voice
        self.controls = {**self.controls, **controls}
        return self
