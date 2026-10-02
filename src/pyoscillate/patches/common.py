from __future__ import annotations

import math
import random
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, ClassVar

from pyo import PyoObject
from pyo.lib.controls import SigTo
from pyo.lib.filters import Hilbert
from pyo.lib.generators import Sine
from pyo.lib.tables import ExpTable, LinTable
from pyo.lib.triggers import Trig, TrigEnv

from pyoscillate.clock import Clock, Division, NoteDivision
from pyoscillate.patches.base import BuildContext, Patch, Sequencer
from pyoscillate.patches.params import Param
from pyoscillate.tempo import Tempo


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

    def finish(self, voice: PyoObject) -> Patch:
        self.voice = voice
        self._bind()
        return self


def semitone_ratio(semitones: float) -> float:
    """Frequency ratio for a pitch shift of `semitones`, for detuning an
    oscillator relative to a body/root frequency."""
    return 2 ** (semitones / 12)


@dataclass(frozen=True)
class Step:
    """One sequencer step: its `index` within the cycle, whether the pattern
    has a `hit` there, and the pattern's `value` for it (an accent, a pitch
    offset, `True` for a set) - meaningless when `hit` is False."""

    index: int
    hit: bool
    value: Any


class Pulse:
    """One clocked step source: calls `callback` every `steps` clock ticks
    and knows which step of a cycle it is on. `GatedVoice` owns one as its
    main pulse and `Gate` owns another, so a patch can run two independent
    rhythms (a per-bar chord change and a 16th-note chop) off the same shared
    `Clock`. Playing and stopping it joins or leaves the clock's grid.

    The step index comes from `Clock.tick`, never an internal counter, so it
    is the same whenever the owner was built or restarted (see `Division`).
    """

    def __init__(self, clock: Clock, steps: int, callback: Callable[[], None]) -> None:
        self.clock = clock
        self.division = clock.subscribe(steps, callback)

    @property
    def steps(self) -> int:
        return self.division.steps

    @steps.setter
    def steps(self, steps: int) -> None:
        self.division.steps = steps

    @staticmethod
    def step_at(tick: int, steps: int, cycle: int) -> int:
        """The step within a cycle of `cycle` steps at clock `tick`, for a
        pulse firing every `steps` ticks: the one place this is computed."""
        return (tick // steps) % cycle

    def index(self, cycle: int) -> int:
        """The current step within a cycle of `cycle` steps."""
        return self.step_at(self.clock.tick, self.division.steps, cycle)

    def play(self) -> None:
        self.division.play()

    def stop(self) -> None:
        self.division.stop()


class GatedVoice(Patch):
    """Base for a voice articulated by clocked events - a trigger or gate
    opens an envelope on each hit, note, or step (the drums archetype, but
    equally a monophonic bassline's per-note envelope). Concrete voices call
    `self.envelope(...)` instead of hand-pairing `ExpTable`/`TrigEnv`, and
    `self.schedule(...)` instead of hand-wiring `clock.subscribe` and a
    `rate` control - both auto-register their Pyo objects for `resources`,
    so a `build()` can't forget to retain one (the crash risk
    `patches/AGENTS.md`'s resource-ownership rule exists to prevent).
    """

    # set by `schedule()`/`schedule_steps()` during `build()`
    _pulse: Pulse
    _division: Division
    _clock: Clock
    _base_division: NoteDivision
    _scheduled: bool

    def _reset(self) -> None:
        """Call at the top of `build()`: fresh Pyo objects and a fresh
        resources/controls list every call, since one voice instance's
        `build()` may run again on a rebuild."""
        super()._reset()
        self.trigger = Trig().stop()
        self.retain(self.trigger)
        self._scheduled = False

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

    def next_step(self) -> None:
        """Per-tick hook for a scheduled voice: `schedule()`'s default
        callback. A concrete voice overrides this instead of defining a
        `build()`-local closure, reading whatever graph nodes and clock
        state it needs off `self` (`self._clock`, `self._division`, and any
        node `build()` assigned) - the same hook-method shape as `tone()`/
        `voice_graph()` for a style that needs genuinely different behavior
        (`patches/AGENTS.md`'s design rule 1)."""
        raise NotImplementedError

    def schedule(
        self, base_division: NoteDivision, rate: float, clock: Clock
    ) -> Division:
        """Subscribe `self.next_step` on `clock`; the `rate` `Param`'s
        control later re-spaces it through `reschedule()`."""
        return self.schedule_with(base_division, rate, clock, self.next_step)

    def schedule_with(
        self,
        base_division: NoteDivision,
        rate: float,
        clock: Clock,
        callback: Callable[[], None],
    ) -> Division:
        """`schedule()` with an explicit per-tick `callback`."""
        self._base_division = base_division
        return self.schedule_steps(
            clock, clock.ticks_for_rate(base_division, rate), callback
        )

    def schedule_steps(
        self, clock: Clock, steps: int, callback: Callable[[], None]
    ) -> Division:
        """Subscribe `callback` every `steps` raw ticks, for a voice whose
        timing isn't a `NoteDivision` rate (a bar-synced swell, a
        step-division count)."""
        self._pulse = Pulse(clock, steps, callback)
        self._division = self._pulse.division
        self._clock = clock
        self._scheduled = True
        return self._division

    def reschedule(self, rate: float) -> None:
        """Live `rate` control: re-space the scheduled division."""
        self._division.steps = self._clock.ticks_for_rate(self._base_division, rate)

    def step_pattern(
        self, cycle: int, pattern: dict[int, Any] | set[int]
    ) -> Callable[[], Step]:
        """Zero-arg callable for a `schedule()` callback: derives the current
        step (mod `cycle`) from the shared clock's own tick, not an internal
        counter that starts at 0 whenever this patch is (re)built - the same
        reasoning as `Clock.tick`'s docstring. Returns a `Step`: `hit` is
        whether `step` is in the pattern and `value` is `pattern[step]` for a
        dict (`True` for a set). The concrete voice's own callback wraps this
        to decide what a hit does (trigger, reset, accent, recompute pitch,
        ...).

        Call only after `self.schedule(...)` has run (`self._division` and
        `self._clock` must exist), which every `build()` already does before
        its callback can fire."""

        def check() -> Step:
            index = Pulse.step_at(self._clock.tick, self._division.steps, cycle)
            if isinstance(pattern, dict):
                return Step(index, index in pattern, pattern.get(index, 0.0))
            return Step(index, index in pattern, True)

        return check

    def finish(self, voice: PyoObject, *, resources: tuple[Any, ...] = ()) -> Patch:
        """Terminal step of `build()`: retain any further `resources` build()
        kept only as locals (graph nodes stored on `self` are retained
        automatically), then wire `sequencer`/`voice`, run every `Param`
        control, and return `self` now that it's built."""
        if not self._scheduled:
            raise RuntimeError(
                f"{type(self).__name__}.build() never called self.schedule(...)"
            )
        self.retain(*resources)
        self.sequencer = self._division
        self.voice = voice
        self._bind()
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


class Gate(Patch):
    """Opt-in add-on that chops a voice's output into clocked pulses (see
    `patches/AGENTS.md`, "Gate add-on"). Mix it in ahead of the voice base -
    `class Strings(Gate, GatedVoice)` - and call `self.add_gate(source,
    context)` in `build()`, then pass the result to `finish()`.

    It owns its `Param`s and its own clock subscription, merged into the
    voice's sequencer by `finish()`. The gate is always built: `gate` is the
    depth of the chop, and 0 leaves the sound untouched without a rebuild.
    """

    # pulse slots per cycle: one bar at the default 16th-note rate
    GATE_STEPS: ClassVar[int] = 16
    # fraction of one pulse spent ramping up and down, so edges never click
    GATE_ATTACK: ClassVar[float] = 0.05
    GATE_RELEASE: ClassVar[float] = 0.15

    # the gate's graph, assigned by add_gate(); finish() retains each one
    gate_trigger: Trig
    gate_table: LinTable
    gate_env: TrigEnv
    gate_amount_sig: SigTo
    gate_closed: PyoObject
    gate_cut: PyoObject
    gate_gain: PyoObject
    gate_output: PyoObject
    _gate_pulse: Pulse
    _gate_tempo: Tempo
    _gated: bool

    gate = Param(
        0.0,
        1.0,
        0.05,
        0.0,
        "Gate",
        "How hard the sound is chopped into rhythmic pulses; zero leaves it smooth, full cuts it "
        "completely silent between pulses.",
        sweep=True,
    )

    @Param(
        0.1,
        1.0,
        0.05,
        0.7,
        "Pulse length",
        "How much of each step the sound stays open; short is clipped and staccato, long is nearly "
        "held.",
    )
    def gate_length(self, value: float) -> None:
        self.retime_gate()

    gate_density = Param(
        0.0,
        1.0,
        0.05,
        1.0,
        "Pulse density",
        "How many of the steps play; full pulses on every step, lower drops steps at random (the same "
        "ones for a given Pattern).",
    )
    gate_seed = Param(
        0,
        99,
        1,
        0,
        "Pattern",
        "Picks which steps drop out when Pulse density is below full; each number is a different "
        "rhythm.",
    )

    @Param(
        *Clock.rate_limits(NoteDivision.SIXTEENTH),
        1,
        0,
        "Pulse rate",
        "Speeds the pulses up or slows them down in whole note divisions from sixteenth notes.",
    )
    def gate_rate(self, value: float) -> None:
        self._gate_pulse.steps = self._gate_pulse.clock.ticks_for_rate(
            NoteDivision.SIXTEENTH, value
        )
        self.retime_gate()

    def _reset(self) -> None:
        super()._reset()
        self._gated = False

    def add_gate(self, source: PyoObject, context: BuildContext) -> PyoObject:
        """Chop `source` with the gate and return the result. Call before
        `finish()`; every gate node lives on `self`."""
        self._gate_tempo = context.tempo
        self.gate_trigger = Trig().stop()
        # unity from a short ramp up, held, then a ramp down to silence
        self.gate_table = LinTable(
            [
                (0, 0.0),
                (round(TABLE_SIZE * self.GATE_ATTACK), 1.0),
                (round(TABLE_SIZE * (1 - self.GATE_RELEASE)), 1.0),
                (TABLE_SIZE - 1, 0.0),
            ]
        )
        self.gate_env = TrigEnv(self.gate_trigger, self.gate_table, dur=0.1)
        self.gate_amount_sig = self.live(type(self).gate, time=0.05)
        self.gate_closed = 1 - self.gate_env
        self.gate_cut = self.gate_amount_sig * self.gate_closed
        self.gate_gain = 1 - self.gate_cut
        self.gate_output = source * self.gate_gain
        self._gate_pulse = Pulse(
            context.clock,
            context.clock.ticks_for_rate(NoteDivision.SIXTEENTH, self.gate_rate),
            self.next_gate_step,
        )
        self._gated = True
        return self.gate_output

    def retime_gate(self) -> None:
        """Set the pulse duration from its length, rate and the tempo."""
        step_seconds = (
            self._gate_tempo.bar
            * self._gate_pulse.steps
            / self._gate_pulse.clock.ticks_per_bar
        )
        self.gate_env.dur = step_seconds * self.gate_length

    def gate_hit(self, index: int) -> bool:
        """Whether pulse `index` plays: the same answer for a given Pattern
        and density, so the rhythm repeats every cycle."""
        draw = random.Random(self.gate_seed * self.GATE_STEPS + index).random()
        return draw < self.gate_density

    def next_gate_step(self) -> None:
        index = self._gate_pulse.index(self.GATE_STEPS)
        if self.gate_hit(index):
            self.gate_trigger.play()

    def finish(self, voice: PyoObject, **kwargs: Any) -> Patch:
        """The voice base's `finish()`, then the gate's clock subscription
        joins the voice's own sequencer so both start and stop together."""
        if not self._gated:
            raise RuntimeError(
                f"{type(self).__name__}.build() never called self.add_gate(...)"
            )
        patch = super().finish(voice, **kwargs)  # type: ignore[misc]
        self.sequencer = SequencerGroup((self.sequencer, self._gate_pulse))
        return patch


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
