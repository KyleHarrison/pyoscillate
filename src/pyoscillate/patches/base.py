from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, ClassVar, Protocol

from pyo import PyoObject
from pyo.lib._core import PyoObjectBase
from pyo.lib.controls import SigTo
from pyo.lib.dynamics import Clip, Compress
from pyo.lib.server import Server, pa_list_devices

from pyoscillate.patches.params import Param, SliderSpec

# ramp-to-silence time before a stopped patch's objects are actually cut, so
# stop() never truncates a voice mid-sample and produces a click/pop
STOP_FADE = 0.2
# Absolute peak cap for a single patch before it reaches the shared hardware
# output. The Flet rack adds a separate, capped master gain for the sum.
PATCH_OUTPUT_CEILING = 0.18


def start_server(
    *,
    output_device: int | None = None,
    nchnls: int = 2,
    audio: str = "portaudio",
) -> Server:
    """Start a Pyo server or raise before any audio objects can be built."""
    server = Server(nchnls=nchnls, duplex=0, audio=audio)
    if output_device is not None:
        server.setOutputDevice(output_device)

    try:
        server.boot()
        if not server.getIsBooted():
            raise RuntimeError(
                f"Pyo could not boot the {audio!r} audio backend"
                + (f" with output device {output_device}" if output_device is not None else "")
            )
        server.start()
        if not server.getIsStarted():
            raise RuntimeError(f"Pyo booted but could not start the {audio!r} audio backend")
    except Exception:
        if server.getIsStarted():
            server.stop()
        if server.getIsBooted():
            server.shutdown()
        raise
    return server


def setup_notebook(
    *,
    output_device: int | None = None,
    nchnls: int = 2,
) -> Server:
    """Create, boot, and start the Pyo server for notebook use.

    `output_device` should match the output index reported by
    `pa_list_devices()`.
    """
    pa_list_devices()
    return start_server(output_device=output_device, nchnls=nchnls)


class Sequencer(Protocol):
    """Anything a `Patch` can start/stop ticking - a `Clock` `Division`, a
    raw pyo `Pattern`, or clock_tick's multi-`Pattern` fan-out."""

    def play(self) -> None: ...
    def stop(self) -> None: ...


def _slugify(class_name: str) -> str:
    """CamelCase class name -> snake_case rack key, e.g. `KickRound` ->
    `kick_round`. A subclass overrides this default by assigning a plain
    `name = "..."` class attribute, which shadows the `Patch.name` property
    below without needing to touch it."""
    chars: list[str] = []
    for index, char in enumerate(class_name):
        if char.isupper() and index > 0:
            chars.append("_")
        chars.append(char.lower())
    return "".join(chars)


def _humanize(class_name: str) -> str:
    """CamelCase class name -> UI title, joining each capitalized word with
    " - ": `KickRound` -> "Kick - Round", `Clap` -> "Clap". A subclass
    overrides this default the same way as `name` (see `_slugify`)."""
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


@dataclass(frozen=True)
class SidechainSource:
    """Ducks a patch's output off another rack patch's live voice signal -
    e.g. a kick ducking the bass on every hit.

    The connection is resolved at the ducked patch's own build time: if
    `patch_name` isn't already built (its switch was never turned on) when
    the ducked patch is (re)built, it plays unducked. Turning the source on
    afterward doesn't retroactively rewire an already-built target; toggle
    the ducked patch again to pick it up. Making that reactive is future
    work.
    """

    patch_name: str
    depth: float = 0.6
    release: float = 0.15


class Patch(ABC):
    """A patch's live definition *and*, once built, the thing actually
    playing: owns `parameters`/`volume_default`/`rebuild_parameters`/
    `needs_*` as class attributes, wires the DSP graph onto `self` in
    `build()`, and drives it with `start()`/`stop()`/`set()`/`update()`. A
    project rack lists instances of this class directly - `name`/`title`/
    `summary`/`sidechain` all live on the instance rather than being restated
    in a separate wrapper.
    """

    parameters: ClassVar[tuple[SliderSpec, ...]] = ()
    _parameter_names: ClassVar[frozenset[str]] = frozenset()
    volume_default: ClassVar[float] = 0.6
    rebuild_parameters: ClassVar[tuple[str, ...]] = ()
    needs_tempo: ClassVar[bool] = False
    needs_clock: ClassVar[bool] = False
    needs_harmony: ClassVar[bool] = False

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Auto-derive `parameters` from the `Param`s (or legacy
        `SliderSpec`s) a subclass declares as class attributes, merged onto
        the inherited ones: a redeclared name (`punch =
        Kick.punch.replace(default=1.4)`) replaces its spec in place, a new
        name is appended. A class with none of its own keeps its parent's."""
        super().__init_subclass__(**kwargs)
        merged = {spec.name: spec for spec in cls.parameters}
        for value in vars(cls).values():
            if isinstance(value, Param):
                merged[value.name] = value.spec
            elif isinstance(value, SliderSpec):
                merged[value.name] = value
        cls.parameters = tuple(merged.values())
        cls._parameter_names = frozenset(merged)

    def __init__(
        self,
        *,
        sidechain: SidechainSource | None = None,
        name: str | None = None,
        title: str | None = None,
        summary: str | None = None,
        **values: Any,
    ) -> None:
        """Seed this instance's current parameter values from `parameters`'
        defaults, overridden by any `values` given - so two instances of the
        same class can hold independent current settings instead of sharing
        behavior baked into `build()`'s own defaults - then set up fresh
        build/lifecycle state. `sidechain`/`name`/`title`/`summary` are only
        ever restated at the rack call site when a project needs one to
        differ from this instance's own default."""
        self.resources: list[Any] = []
        self.controls: dict[str, Callable[[Any], None]] = {}
        self.sequencer: Sequencer | None = None
        self.voice: PyoObject | None = None
        self.volume: float = self.volume_default
        self._output: PyoObject | None = None
        self._fade: SigTo | None = None
        self._volume_control: SigTo | None = None
        self._output_resources: tuple[PyoObject, ...] = ()
        self._built = False
        self._playing = False
        self._retired: tuple[Any, ...] = ()
        self.sidechain = sidechain
        for spec in self.parameters:
            setattr(self, spec.name, spec.default)
        self.configure(**values)
        # plain instance attributes, distinct from the `name`/`title`/
        # `summary` properties below - a style subclass that shadows one of
        # those properties with its own plain `title = "..."` class
        # attribute (see the property docstrings) makes that property
        # unreachable for its instances, so setting `self._title` alone
        # wouldn't be seen; going through the property setters below instead
        # (only when a constructor override was actually given, so an
        # un-given one doesn't plant a stale `None` in `self.__dict__` ahead
        # of a shadowing class attribute) writes an instance attribute that
        # outranks that class attribute on lookup either way.
        self._name: str | None = None
        self._title: str | None = None
        self._summary: str | None = None
        if name is not None:
            self.name = name
        if title is not None:
            self.title = title
        if summary is not None:
            self.summary = summary

    @property
    def name(self) -> str:
        """Rack key for this instance; a subclass overrides this with a
        plain `name = "..."` class attribute when the humanized class name
        isn't the right rack key (e.g. a style subclass whose class name
        doesn't mention its family)."""
        return self._name if self._name is not None else _slugify(type(self).__name__)

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @property
    def title(self) -> str:
        """Rack-facing label; override the same way as `name` when the
        humanized class name isn't the right UI copy."""
        return self._title if self._title is not None else _humanize(type(self).__name__)

    @title.setter
    def title(self, value: str) -> None:
        self._title = value

    @property
    def summary(self) -> str:
        """One-line rack description, defaulting to this class's own
        docstring so a project rack module doesn't have to say the same
        thing twice. Override with a plain `summary = "..."` class
        attribute when the docstring is written for developers, not the UI.
        """
        return (
            self._summary
            if self._summary is not None
            else " ".join((type(self).__doc__ or "").split())
        )

    @summary.setter
    def summary(self, value: str) -> None:
        self._summary = value

    def retain(self, *objects: Any) -> None:
        """Keep `objects` alive for the lifetime of the built patch."""
        self.resources.extend(objects)

    def configure(self, **values: Any) -> None:
        """Update several of this instance's current parameter values via
        `set()` - e.g. loading a preset. Unlike `set()`, an unknown name is
        silently skipped rather than raising, since a caller here is often
        handing over a superset of names (a full preset, `__init__`'s
        constructor kwargs) that only partly applies to this instance."""
        for name, value in values.items():
            if name in self._parameter_names:
                self.set(name, value)

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
            self.voice,
            self.sequencer,
            self._output,
            self._output_resources,
            self._fade,
            self._volume_control,
        )
        self.resources = []
        self.controls = {}
        self._built = False

    def _bind(self) -> None:
        """Call from `finish()`: retain every public Pyo object `build()`
        stored on `self`, mark the graph built, and run every `Param`
        control once with its current value."""
        retained = {id(obj) for obj in self.resources} | {id(self.voice)}
        for key, value in vars(self).items():
            if (
                not key.startswith("_")
                and isinstance(value, PyoObjectBase)
                and id(value) not in retained
            ):
                self.resources.append(value)
        self._built = True
        for spec in self.parameters:
            param = getattr(type(self), spec.name, None)
            if isinstance(param, Param) and param.control is not None:
                param.control(self, getattr(self, spec.name))

    @abstractmethod
    def build(self, **kwargs: Any) -> Patch: ...

    def set(self, name: str, value: Any) -> None:
        """Update one parameter: always keeps `self.<name>` current (so a
        later `build()` sees it without needing the value restated), and
        additionally pushes it into the running Pyo graph when `finish()`
        registered a live control under `name`. Setting a `rebuild_parameters`
        name (no live control) just stages the new value for the next
        `build()` - the caller decides whether that rebuild happens."""
        if name == "volume":
            self.volume = value
            if self._volume_control is not None:
                self._volume_control.value = value
            return
        if name not in self._parameter_names:
            raise KeyError(f"{type(self).__name__} has no parameter named {name!r}")
        setattr(self, name, value)
        setter = self.controls.get(name)
        if setter is not None:
            setter(value)

    def update(self, values: dict[str, Any]) -> Patch:
        """Update several live parameters and preserve runtime state."""
        for name, value in values.items():
            self.set(name, value)
        return self

    def on_evolve(self, index: int) -> None:
        """Hook for a rack-level `GroupController`: called live, every N
        bars, on whichever patch instance is currently active in a watched
        group. `index` is the controller's own fire count. A no-op by
        default; deliberately not a `@Param` - no slider, no preset entry,
        not user-facing - a plain live method call driven by the
        controller's timer instead of a widget, the same relationship the
        UI sliders already have to `set()`. An override owns its own index
        wraparound (e.g. `index % len(self.SOMETHING)`)."""

    def start(self) -> Patch:
        # `volume` boosts *before* Compress, not after: Compress's own mul
        # multiplies its already-compressed output, so gain reduction would
        # never see (and never catch) whatever volume pushed past the
        # limiter. Boosting first means the limiter always sees the final
        # level and can catch it regardless of how high volume goes - a
        # thresh near 0dB with a high ratio only engages for whatever
        # `volume` pushes toward clipping, rather than coloring the patch
        # at its normal level.
        self._volume_control = SigTo(value=self.volume, time=0.05)
        boosted = self.voice * self._volume_control
        compressed = Compress(boosted, thresh=-1, ratio=10, risetime=0.001, falltime=0.05)
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
        return self

    def stop(self) -> Patch:
        if not self._playing:
            return self
        self._playing = False
        self.sequencer.stop()
        if self._fade is not None:
            self._fade.value = 0.0
        # delay the hard stop until the fade above has finished ramping to
        # zero, otherwise the underlying objects (and the click) get cut
        # off before the ramp ever reaches silence
        self.voice.stop(wait=STOP_FADE)
        if self._output is not None:
            self._output.stop(wait=STOP_FADE)
        return self


@dataclass
class PatchRack:
    """Keeps the one currently-playing Patch per named voice.

    Rerunning `hat.build(...)` after editing hat.py and reassigning
    `hat_patch` doesn't stop the previous patch - pyo's audio graph keeps
    running until `.stop()` is called explicitly, and once the Python
    variable is overwritten there's no longer any reference to call it on,
    so the old voice plays on forever, unkillable.

    Routing patch cells through a single long-lived rack (create it once in
    the Setup cell, alongside `s` and `tempo`) fixes that: `rack.start(name,
    ...)` always stops whatever was previously registered under `name`
    first, so a rerun can never leave an orphaned voice behind.
    """

    _patches: dict[str, Patch] = field(default_factory=dict)
    _signatures: dict[str, tuple[tuple[Any, ...], dict[str, Any], float]] = field(
        default_factory=dict, repr=False
    )

    def start(self, name: str, patch: Patch) -> Patch:
        self.stop(name)
        self._patches[name] = patch
        return patch.start()

    def get(self, name: str) -> Patch | None:
        """Return the active patch, if any, without changing its state."""
        return self._patches.get(name)

    def stop(self, name: str) -> None:
        self._signatures.pop(name, None)
        existing = self._patches.pop(name, None)
        if existing is not None:
            existing.stop()

    def stop_all(self) -> None:
        for name in list(self._patches):
            self.stop(name)

    def toggle(
        self,
        name: str,
        build: Callable[..., Patch],
        *args: Any,
        volume: float = 1.0,
        **kwargs: Any,
    ) -> Patch | None:
        """Rerun a patch cell to switch it on and off in place.

        Calls `build(*args, **kwargs)` and starts it under `name` - unless a
        patch is already running under `name` that was built from these
        exact same arguments, in which case it's stopped instead and `None`
        is returned. So: run a cell to start a patch, rerun it unchanged to
        stop it, rerun it again to bring it back. Changing an argument while
        the patch is running skips the toggle-off and goes straight to
        stopping the old version and starting the new one, same as
        `start()`.

        `volume` isn't passed to `build` - it's applied to the returned
        `Patch` (see `Patch.volume`) and included in the toggle signature
        like any other argument.
        """
        signature = (args, kwargs, volume)
        if name in self._signatures and self._signatures[name] == signature:
            self.stop(name)
            return None

        patch = build(*args, **kwargs)
        patch.volume = volume
        self.start(name, patch)
        self._signatures[name] = signature
        return patch
