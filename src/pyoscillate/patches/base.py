from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, ClassVar, Protocol

from pyo import PyoObject
from pyo.lib.controls import SigTo
from pyo.lib.dynamics import Clip, Compress
from pyo.lib.server import Server, pa_list_devices

from pyoscillate.patches.params import SliderSpec

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
    """Anything a `BuiltPatch` can start/stop ticking - a `Clock` `Division`,
    a raw pyo `Pattern`, or clock_tick's multi-`Pattern` fan-out."""

    def play(self) -> None: ...
    def stop(self) -> None: ...


@dataclass
class BuiltPatch:
    """A step sequencer paired with the audio chain it drives.

    Building a patch only wires up the pyo object graph - nothing is audible
    or ticking until `start()` is called, and nothing keeps running after
    `stop()`. `resources` strongly retains auxiliary Pyo graph nodes whose
    native DSP objects can otherwise outlive their Python wrappers.
    """

    sequencer: Sequencer
    voice: PyoObject
    controls: dict[str, Callable[[Any], None]] = field(default_factory=dict)
    volume: float = 1.0
    resources: tuple[Any, ...] = field(default=(), repr=False)
    _output: PyoObject | None = field(default=None, repr=False)
    _fade: SigTo | None = field(default=None, repr=False)
    _volume_control: SigTo | None = field(default=None, repr=False)
    _output_resources: tuple[PyoObject, ...] = field(default=(), repr=False)

    def set(self, name: str, value: Any) -> None:
        """Update one live parameter without rebuilding the Pyo graph."""
        if name == "volume":
            self.volume = value
            if self._volume_control is not None:
                self._volume_control.value = value
            return
        try:
            setter = self.controls[name]
        except KeyError as error:
            raise KeyError(f"BuiltPatch has no live parameter named {name!r}") from error
        setter(value)

    def update(self, values: dict[str, Any]) -> BuiltPatch:
        """Update several live parameters and preserve runtime state."""
        for name, value in values.items():
            self.set(name, value)
        return self

    def start(self) -> BuiltPatch:
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
        return self

    def stop(self) -> BuiltPatch:
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


class Patch(ABC):
    """Base for a patch's live definition: owns `parameters`/`volume_default`/
    `rebuild_parameters`/`needs_*` as class attributes and builds the DSP
    graph in `build()`. A `PatchDef` reads everything it needs directly off
    an instance instead of having it restated at the call site.
    """

    parameters: ClassVar[tuple[SliderSpec, ...]]
    volume_default: ClassVar[float] = 0.6
    rebuild_parameters: ClassVar[tuple[str, ...]] = ()
    needs_tempo: ClassVar[bool] = False
    needs_clock: ClassVar[bool] = False
    needs_harmony: ClassVar[bool] = False

    @abstractmethod
    def build(self, **kwargs: Any) -> BuiltPatch: ...


@dataclass
class FunctionVoice(Patch):
    """Adapts an unmigrated `build()`/`PARAMETERS` module to the `Patch`
    contract, so a `PatchDef` only ever needs a `Patch` instance regardless
    of whether a given patch has moved to a class yet.
    """

    _build: Callable[..., BuiltPatch]
    parameters: tuple[SliderSpec, ...]
    volume_default: float = 0.6
    rebuild_parameters: tuple[str, ...] = ()
    needs_tempo: bool = False
    needs_clock: bool = False
    needs_harmony: bool = False

    def build(self, **kwargs: Any) -> BuiltPatch:
        return self._build(**kwargs)

    @classmethod
    def from_module(
        cls,
        module: Any,
        *,
        volume_default: float,
        style: str | None = None,
        **flags: Any,
    ) -> FunctionVoice:
        """`style` selects a `make_builder(style)` variant; omit it for a
        module with a single `build`. `volume_default` is always required
        explicitly, since not every module defines its own `VOLUME_DEFAULT`
        constant and callers already choose a rack-specific value today.
        `flags` are the remaining `Patch` fields (`needs_tempo=True`, and so
        on)."""
        build = module.make_builder(style) if style is not None else module.build
        return cls(build, module.PARAMETERS, volume_default, **flags)


@dataclass
class PatchRack:
    """Keeps the one currently-playing BuiltPatch per named voice.

    Rerunning `hat.build(...)` after editing hat.py and reassigning
    `hat_patch` doesn't stop the previous BuiltPatch - pyo's audio graph
    keeps running until `.stop()` is called explicitly, and once the Python
    variable is overwritten there's no longer any reference to call it on,
    so the old voice plays on forever, unkillable.

    Routing patch cells through a single long-lived rack (create it once in
    the Setup cell, alongside `s` and `tempo`) fixes that: `rack.start(name,
    ...)` always stops whatever was previously registered under `name`
    first, so a rerun can never leave an orphaned voice behind.
    """

    _patches: dict[str, BuiltPatch] = field(default_factory=dict)
    _signatures: dict[str, tuple[tuple[Any, ...], dict[str, Any], float]] = field(
        default_factory=dict, repr=False
    )

    def start(self, name: str, patch: BuiltPatch) -> BuiltPatch:
        self.stop(name)
        self._patches[name] = patch
        return patch.start()

    def get(self, name: str) -> BuiltPatch | None:
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
        build: Callable[..., BuiltPatch],
        *args: Any,
        volume: float = 1.0,
        **kwargs: Any,
    ) -> BuiltPatch | None:
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
        `BuiltPatch` (see `BuiltPatch.volume`) and included in the toggle
        signature like any other argument.
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
