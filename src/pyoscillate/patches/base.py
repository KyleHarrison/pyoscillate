from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, ClassVar, Protocol

from pyo import PyoObject
from pyo.lib._core import PyoObjectBase, PyoPVObject
from pyo.lib.analysis import Follower2
from pyo.lib.controls import SigTo
from pyo.lib.dynamics import Clip, Compress
from pyo.lib.generators import Sine
from pyo.lib.server import Server

from pyoscillate.clock import Clock
from pyoscillate.harmony import Harmony
from pyoscillate.patches.evolve import Evolution, Evolve
from pyoscillate.patches.params import Param
from pyoscillate.patches.sweep import ParamSweep, Sweep
from pyoscillate.tempo import Tempo

# ramp-to-silence time before a stopped patch's objects are actually cut, so
# stop() never truncates a voice mid-sample and produces a click/pop
STOP_FADE = 0.2
# Absolute peak cap for a single patch before it reaches the shared hardware
# output. The Flet rack adds a separate, capped master gain for the sum.
PATCH_OUTPUT_CEILING = 0.18


def start_server(*, nchnls: int = 2, audio: str = "portaudio") -> Server:
    """Start a Pyo server or raise before any audio objects can be built."""
    server = Server(nchnls=nchnls, duplex=0, audio=audio)
    try:
        server.boot()
        if not server.getIsBooted():
            raise RuntimeError(f"Pyo could not boot the {audio!r} audio backend")
        server.start()
        if not server.getIsStarted():
            raise RuntimeError(
                f"Pyo booted but could not start the {audio!r} audio backend"
            )
    except Exception:
        if server.getIsStarted():
            server.stop()
        if server.getIsBooted():
            server.shutdown()
        raise
    return server


class Sequencer(Protocol):
    """Anything a `Patch` can start/stop ticking - a `Clock` `Division`, a
    raw pyo `Pattern`, or clock_tick's multi-`Pattern` fan-out."""

    def play(self) -> None: ...
    def stop(self) -> None: ...


@dataclass(frozen=True)
class BuildContext:
    """Everything a patch's `build()` may draw on, always fully populated by
    the rack that runs it: the shared `tempo`, the master `clock`, and the
    rack's `harmony`. A patch reads the parts it uses and ignores the rest,
    so there is no per-patch "needs" declaration and nothing optional."""

    tempo: Tempo
    clock: Clock
    harmony: Harmony


class PlayingGroup(Protocol):
    """A rack group at runtime: knows which of its patches are playing."""

    def playing_patches(self) -> tuple[Patch, ...]: ...


@dataclass(frozen=True)
class Sidechain:
    """Ducks a patch's output off another rack group's currently playing
    voice signal - e.g. a kick ducking the bass on every hit. A rack declares
    these with `SidechainSource` and binds them to its own runtime groups, so
    the duck follows whichever patches are playing in that group (a kick style
    switch doesn't silently un-wire it).

    The connection is made when the ducked patch starts: a source group with
    nothing playing then leaves the patch unducked. Turning the source on
    afterward doesn't retroactively rewire an already-started target; toggle
    the ducked patch again to pick it up.
    """

    group: PlayingGroup
    depth: float
    release: float


class Patch(ABC):
    """A patch's live definition *and*, once built, the thing actually
    playing: owns its `Param`s and `volume` as class attributes, wires the DSP
    graph onto `self` in `build()`, and drives it with `start()`/`stop()`. A
    project rack lists instances of this class directly - `name`/`title`/
    `summary` live on the class (derived from the class name and docstring
    unless the class body assigns its own) rather than in a wrapper.

    Every parameter, including `volume`, is a `Param` descriptor: read and
    write it as an attribute (`patch.volume = 0.5`). Assigning stores the
    value and, once built, pushes it into the running graph.
    """

    name: ClassVar[str]
    title: ClassVar[str]
    summary: ClassVar[str]
    params: ClassVar[tuple[Param, ...]] = ()
    rebuild_params: ClassVar[tuple[Param, ...]] = ()

    # the running graph's own state, assigned by `build()`/`finish()`/`start()`
    voice: PyoObject
    sequencer: Sequencer
    volume_signal: SigTo
    _fade: SigTo
    _output: PyoObject
    _output_resources: tuple[PyoObject, ...]

    @Param(
        0.0,
        2.0,
        0.1,
        0.6,
        "Output level",
        "Overall level of this voice before it reaches the shared output.",
    )
    def volume(self, value: float) -> None:
        self.volume_signal.value = value

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Collect every `Param` along the MRO (a redeclared name replaces
        its parent's in place, a new one is appended) into `params`, with the
        named-choice (dropdown) params first, and derive `name`/`title`/`summary` from the class itself unless its body
        assigns them."""
        super().__init_subclass__(**kwargs)
        merged: dict[str, Param] = {}
        for klass in reversed(cls.__mro__):
            for value in vars(klass).values():
                if isinstance(value, Param):
                    merged[value.name] = value
        cls.params = tuple(
            sorted(merged.values(), key=lambda param: not param.spec.options)
        )
        cls.rebuild_params = tuple(param for param in cls.params if param.rebuild)
        if "name" not in vars(cls):
            cls.name = cls.slugify(cls.__name__)
        if "title" not in vars(cls):
            cls.title = cls.humanize(cls.__name__)
        if "summary" not in vars(cls):
            cls.summary = " ".join((cls.__doc__ or "").split())

    @staticmethod
    def slugify(class_name: str) -> str:
        """CamelCase class name -> snake_case rack key, e.g. `KickRound` ->
        `kick_round`."""
        chars: list[str] = []
        for index, char in enumerate(class_name):
            if char.isupper() and index > 0:
                chars.append("_")
            chars.append(char.lower())
        return "".join(chars)

    @staticmethod
    def humanize(class_name: str) -> str:
        """CamelCase class name -> UI title, joining each capitalized word
        with " - ": `KickRound` -> "Kick - Round", `Clap` -> "Clap"."""
        words: list[str] = []
        current = ""
        for char in class_name:
            if char.isupper() and current:
                words.append(current)
                current = char
            else:
                current += char
        if current:
            words.append(current)
        return " - ".join(words)

    def __init__(self, **values: float) -> None:
        """Seed every `Param` from its default, overridden by the matching
        keyword in `values` (so two instances of one class hold independent
        settings). Fresh build/lifecycle state is set up; no control runs and
        no Pyo object is created until `build()`."""
        self.resources: list[Any] = []
        self.live_signals: dict[Param, SigTo] = {}
        self.sidechains: tuple[Sidechain, ...] = ()
        self._tempo_links: list[Callable[[], None]] = []
        self.sweeps: dict[Param, Sweep] = {
            param: Sweep(self, param) for param in self.params if param.sweep
        }
        # the rack tempo the patch was last started with; sweeps sync to it
        self.tempo: Tempo | None = None
        self._built = False
        self._playing = False
        self._retired: tuple[Any, ...] = ()
        for param in self.params:
            param.write(self, values.pop(param.name, param.default))
        if values:
            raise TypeError(
                f"{type(self).__name__} has no parameter(s) {sorted(values)}"
            )
        # the patch's own `on_evolve` timer, then one per dropdown it can
        # rotate (see `evolution_axes`)
        self.evolution = Evolution(self)
        self.axis_evolutions: dict[Param, Evolution] = {
            axis: Evolution(self, axis) for axis in self.evolution_axes()
        }

    @property
    def built(self) -> bool:
        return self._built

    @property
    def playing(self) -> bool:
        return self._playing

    def retain(self, *objects: Any) -> None:
        """Keep `objects` alive for the lifetime of the built patch."""
        self.resources.extend(objects)

    def live(self, param: Param, *, time: float = 0.15) -> SigTo:
        """A retained `SigTo` that follows `param`: assigning the parameter
        afterwards glides this signal, so a graph node can take it directly
        with no control method."""
        signal = SigTo(value=param.read(self), time=time)
        self.retain(signal)
        self.live_signals[param] = signal
        return signal

    def sync(self, tempo: Tempo, apply: Callable[[Tempo], None]) -> None:
        """Run `apply(tempo)` now and again on every `retempo()`. Use it for
        any value derived from a note length (an envelope `dur`, an LFO rate,
        a delay time) instead of computing it once in `build()`, so a BPM
        change reaches the running graph. `apply` may read `Param`s: it is
        replayed with their current values."""
        apply(tempo)
        self._tempo_links.append(lambda: apply(tempo))

    def tempo_sine(
        self, tempo: Tempo, period: Callable[[Tempo], float], **kwargs: Any
    ) -> Sine:
        """A retained `Sine` LFO whose period (seconds, from `period(tempo)`)
        follows the tempo, e.g. `period=lambda t: t.bar * 4`."""
        lfo = Sine(freq=1 / period(tempo), **kwargs)
        self.retain(lfo)
        self.sync(tempo, lambda t: setattr(lfo, "freq", 1 / period(t)))
        return lfo

    def retempo(self) -> None:
        """Recompute every `sync()`ed value and sweep length after the
        shared `Tempo` changed. Safe on a built patch, playing or not."""
        for link in self._tempo_links:
            link()
        for sweep in self.sweeps.values():
            sweep.retempo()

    def sweep_for(self, param: Param) -> Sweep:
        """This patch's `Sweep` for `param`, recognised across style
        overrides (see `Param.origin`)."""
        for own, sweep in self.sweeps.items():
            if own.origin is param.origin:
                return sweep
        raise LookupError(f"{type(self).__name__}: {param.name} has no sweep")

    def declare_sweeps(self, sweeps: tuple[ParamSweep, ...]) -> None:
        """Start the given sweeps enabled, before the patch is built."""
        for declared in sweeps:
            self.sweep_for(declared.param).declare(declared)

    def apply_param(self, param: Param, value: float) -> None:
        """Push one changed parameter into the built graph."""
        param.control(self, value)
        if param in self.live_signals:
            self.live_signals[param].value = value

    def _reset(self) -> None:
        """Call at the top of `build()`: fresh bookkeeping for a build that
        may run again on the same instance (a rebuild). A graph still
        playing is stopped here, since the caller can no longer reach it
        once `build()` replaces it, and is kept alive (until the next
        rebuild) so its fade-out never runs on collected objects."""
        if self._playing:
            self.stop()
        self._retired = (
            self.resources,
            tuple(value for key, value in vars(self).items() if key != "_retired"),
        )
        self.resources = []
        self.live_signals = {}
        self._tempo_links = []
        self._built = False

    def _bind(self) -> None:
        """Call from `finish()`: retain every public Pyo object `build()`
        stored on `self`, mark the graph built, and run every `Param`
        control once with its current value."""
        self.volume_signal = SigTo(value=self.volume, time=0.05)
        retained = {id(obj) for obj in self.resources} | {id(self.voice)}
        for key, value in vars(self).items():
            if (
                not key.startswith("_")
                and isinstance(value, PyoObjectBase)
                and id(value) not in retained
            ):
                self.resources.append(value)
        self._built = True
        for param in self.params:
            param.control(self, param.read(self))

    @abstractmethod
    def build(self, context: BuildContext) -> Patch: ...

    def on_evolve(self, index: int) -> None:
        """Hook for the patch's own `Evolution`: called live, every N bars
        while the listener (or the rack) has evolution enabled and the patch
        is playing. `index` is the number of times it has fired since the
        patch started. A no-op by default; deliberately not a `Param` - no
        slider, not a preset value - just a plain live method call driven by
        the evolution timer. An override owns its own index wraparound (e.g.
        `index % len(self.SOMETHING)`); overriding it is what makes a patch
        `evolvable`."""

    @property
    def has_evolve_hook(self) -> bool:
        """Whether this patch overrides `on_evolve` with a slow change of its
        own."""
        return type(self).on_evolve is not Patch.on_evolve

    @classmethod
    def evolution_axes(cls) -> tuple[Param, ...]:
        """The dropdown `Param`s this patch can rotate on their own timers,
        phrase first; a mixin adds its own."""
        return ()

    @property
    def evolutions(self) -> tuple[Evolution, ...]:
        """Every evolution this patch has something to change for: one per
        rotating dropdown, then the `on_evolve` hook's if it overrides it."""
        return (
            *self.axis_evolutions.values(),
            *((self.evolution,) if self.has_evolve_hook else ()),
        )

    @property
    def evolvable(self) -> bool:
        """Whether this patch has anything to evolve."""
        return bool(self.evolutions)

    def evolution_of(self, axis: Param) -> Evolution:
        """The evolution that rotates `axis`, recognised across style
        overrides (see `Param.origin`)."""
        for own, evolution in self.axis_evolutions.items():
            if own.origin is axis.origin:
                return evolution
        raise LookupError(f"{type(self).__name__}: {axis.name} does not evolve")

    def declare_evolution(self, evolve: Evolve) -> None:
        """Start the given evolution enabled, before the patch is built. Each
        axis takes the choices its dropdown offers. With no choices named,
        the `on_evolve` hook starts (or, for a patch without one, every
        axis); with choices, only the axes they belong to start, and the hook
        too if there is one."""
        named = [
            evolution
            for evolution in self.axis_evolutions.values()
            if evolution.order(evolve.choices)
        ]
        if self.has_evolve_hook:
            named.append(self.evolution)
        for evolution in named or self.axis_evolutions.values():
            evolution.declare(evolve)

    def _every_evolution(self) -> tuple[Evolution, ...]:
        return (self.evolution, *self.axis_evolutions.values())

    def _duck(self) -> None:
        """Duck this patch's voice off each declared sidechain group's
        currently playing patches (see `Sidechain`)."""
        for sidechain in self.sidechains:
            for source in sidechain.group.playing_patches():
                follower = Follower2(source.voice, falltime=sidechain.release)
                duck = 1 - Clip(follower, min=0, max=1) * sidechain.depth
                self.voice = self.voice * duck
                self.retain(follower, duck)

    def start(self, tempo: Tempo | None = None, clock: Clock | None = None) -> Patch:
        """Play the built graph. Given the rack `tempo`, enabled sweeps run
        too, one cycle per their bars; given the rack `clock`, an enabled
        evolution fires on its bar lines."""
        self.tempo = tempo
        self._duck()
        # `volume` boosts *before* Compress, not after: Compress's own mul
        # multiplies its already-compressed output, so gain reduction would
        # never see (and never catch) whatever volume pushed past the
        # limiter. Boosting first means the limiter always sees the final
        # level and can catch it regardless of how high volume goes - a
        # thresh near 0dB with a high ratio only engages for whatever
        # `volume` pushes toward clipping, rather than coloring the patch
        # at its normal level.
        boosted = self.voice * self.volume_signal
        compressed = Compress(
            boosted, thresh=-1, ratio=10, risetime=0.001, falltime=0.05
        )
        limited = Clip(
            compressed,
            min=-PATCH_OUTPUT_CEILING,
            max=PATCH_OUTPUT_CEILING,
        )
        # pyo's stop(wait=...) only delays the hard cutoff, it doesn't fade
        # the signal itself - multiplying by this ramp is what actually
        # brings the level to zero before that cutoff lands, on both this
        # start (from silence) and the next stop() (see below)
        self._fade = SigTo(value=1.0, time=STOP_FADE)
        # mono voices only have one stream, so .out() alone would only reach channel 0
        faded = limited * self._fade
        mixed = faded.mix(2)
        self._output = mixed.out()
        self._output_resources = (boosted, compressed, limited, faded, mixed)
        self.sequencer.play()
        self._playing = True
        for sweep in self.sweeps.values():
            sweep.run()
        for evolution in self._every_evolution():
            evolution.run(clock)
        return self

    def stop(self) -> Patch:
        if not self._playing:
            return self
        self._playing = False
        for sweep in self.sweeps.values():
            sweep.halt()
        for evolution in self._every_evolution():
            evolution.halt()
        self.sequencer.stop()
        self._fade.value = 0.0
        # delay the hard stop until the fade above has finished ramping to
        # zero, otherwise the underlying objects (and the click) get cut
        # off before the ramp ever reaches silence. Every node is stopped,
        # not just the voice: pyo keeps an active object's C stream running
        # after its Python wrapper (and e.g. its table) is freed, so freeing
        # a retired graph with upstream nodes still active segfaults.
        for obj in self._graph_objects():
            obj.stop(wait=STOP_FADE)
        return self

    @property
    def output(self) -> PyoObject | None:
        """The final stereo signal (after volume, limiter and fade, before
        the rack's master gain) for read-only monitoring; None unless playing."""
        return self._output if self._playing else None

    def _graph_objects(self) -> list[PyoObject | PyoPVObject]:
        """Every stoppable Pyo object the current build owns, including
        ones only held in list/tuple attributes."""
        pending: list[Any] = [
            *self.resources,
            *(value for key, value in vars(self).items() if key != "_retired"),
        ]
        seen: set[int] = set()
        found: list[PyoObject | PyoPVObject] = []
        while pending:
            obj = pending.pop()
            if isinstance(obj, (list, tuple)):
                pending.extend(obj)
            elif isinstance(obj, (PyoObject, PyoPVObject)) and id(obj) not in seen:
                seen.add(id(obj))
                found.append(obj)
        return found
