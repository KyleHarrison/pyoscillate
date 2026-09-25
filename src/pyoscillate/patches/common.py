from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, ClassVar

from pyo import PyoObject
from pyo.lib.controls import SigTo
from pyo.lib.filters import Hilbert
from pyo.lib.generators import Sine
from pyo.lib.tables import ExpTable
from pyo.lib.triggers import Trig, TrigEnv

from pyoscillate.clock import Clock, Division, NoteDivision
from pyoscillate.patches.base import Patch, Sequencer


@dataclass(eq=False)
class ContinuousSequencer:
    """No-op `Sequencer` for psyambient's purely continuous, non-triggered patches.

    These pads are wired entirely from free-running modulators (chaotic
    attractors, LFOs) feeding a generator's parameters directly - once the
    pyo objects exist they process every buffer on their own, with nothing
    that needs a `Pattern`/`Metro` to start or stop ticking. `Patch.start()`/
    `stop()` still call `play()`/`stop()` on a `Sequencer`, so this just
    satisfies that protocol with nothing to actually do.
    """

    def play(self) -> None:
        pass

    def stop(self) -> None:
        pass


class ContinuousVoice(Patch):
    """Base for an ungated, free-running voice (tonal/drone, texture, ...):
    the graph runs from the moment it's built - there's no trigger-to-
    envelope path - so a concrete voice only ever has to describe its own
    graph, calling `self.live(...)` per parameter instead of hand-building a
    `SigTo` and a matching `controls` entry, and `self.finish(voice)` in
    place of `DrumVoice`'s trigger/schedule-flavored `finish`.
    """

    def _reset(self) -> None:
        super()._reset()
        self.sequencer = ContinuousSequencer()

    def live(self, name: str, value: float, *, time: float = 0.15) -> SigTo:
        """A `SigTo` for one named live parameter; auto-registers its
        `controls[name]` setter and retains it."""
        control = SigTo(value=value, time=time)
        self.retain(control)
        self.controls[name] = lambda v: setattr(control, "value", v)
        return control

    def live_all(self, *names: str, time: float = 0.15) -> dict[str, SigTo]:
        """`self.live(...)` for each of `names`, reading each one's current
        value off `self` - the common case where every parameter just needs
        a plain live `SigTo` with no extra wiring."""
        return {name: self.live(name, getattr(self, name), time=time) for name in names}

    def finish(self, voice: PyoObject) -> Patch:
        self.voice = voice
        return self


def semitone_ratio(semitones: float) -> float:
    """Frequency ratio for a pitch shift of `semitones`, for detuning an
    oscillator relative to a body/root frequency."""
    return 2 ** (semitones / 12)


class GatedVoice(Patch):
    """Base for a voice articulated by clocked events - a trigger or gate
    opens an envelope on each hit, note, or step (the drums archetype, but
    equally a monophonic bassline's per-note envelope). Concrete voices call
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


@dataclass(eq=False)
class SequencerGroup:
    """Starts and stops several sequencers as one - for a patch whose clock
    `Division` also needs a free-running `Pattern` (for example, one that
    rewrites a table) to tick only while the patch is playing."""

    sequencers: tuple[Sequencer, ...]

    def play(self) -> None:
        for sequencer in self.sequencers:
            sequencer.play()

    def stop(self) -> None:
        for sequencer in self.sequencers:
            sequencer.stop()


@dataclass(eq=False)
class Stage:
    """A shared processing stage: its output plus every Pyo object it built,
    for the calling patch to put in its own `resources`."""

    output: PyoObject
    resources: tuple[Any, ...] = field(default=(), repr=False)


# pyo's default table length; break-point indices below are in table samples
TABLE_SIZE = 8192
# e-folds across a decay table: exp(-ln 100) is -40 dB, the level where a
# struck tone reads as gone, so a reader's `dur` is the audible ring time
RING_CURVE = math.log(100)


def decay_points(
    curve: float = RING_CURVE,
    *,
    attack: int = 8,
    points: int = 24,
) -> list[tuple[int, float]]:
    """Break-points for a struck envelope: a rise over `attack` table samples,
    then an exponential fall that is `curve` e-folds down at the end, and 0.

    The shared shape of the FM family's break-point envelopes (pyo example
    x10/01). A `TrigEnv` reading it with `dur` seconds plays it at reader
    frequency 1/dur, so one table fits any note length and a live `dur`
    rescales it without rewriting the table. `TrigEnv` outputs 0 once the
    table ends, so a level that should remain after the fall has to be added
    separately.
    """
    span = TABLE_SIZE - 1 - attack
    fall = [
        (attack + round(span * step / points), math.exp(-curve * step / points))
        for step in range(points)
    ]
    return [(0, 0.0), *fall, (TABLE_SIZE - 1, 0.0)]


def frequency_shift(source: PyoObject, shift: Any) -> Stage:
    """Single-sideband frequency shift: every partial moves by `shift` Hz.

    From the pyo Hilbert example (x06/07): the Hilbert transform splits the
    source into two signals 90 degrees apart, and multiplying them by a
    quadrature sine/cosine pair keeps only the sum sideband. Unlike a pitch
    shift the partials move by a fixed amount, not a ratio, so harmonic
    spacing is lost - small shifts read as slow phasing against the dry
    sound, larger ones as inharmonic, metallic detune. A negative `shift`
    moves the spectrum down.
    """
    hilbert = Hilbert(source)
    # streams [sine, cosine]: phase 0.25 of a cycle is the cosine
    quadrature = Sine(freq=shift, phase=[0, 0.25])
    real_part = hilbert["real"] * quadrature[1]
    imaginary_part = hilbert["imag"] * quadrature[0]
    shifted = real_part + imaginary_part
    return Stage(shifted, (hilbert, quadrature, real_part, imaginary_part))
