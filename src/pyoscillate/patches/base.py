from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

from pyo import PyoObject
from pyo.lib.controls import SigTo
from pyo.lib.dynamics import Compress
from pyo.lib.server import Server, pa_list_devices

# ramp-to-silence time before a stopped patch's objects are actually cut, so
# stop() never truncates a voice mid-sample and produces a click/pop
STOP_FADE = 0.2


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

    server = Server(nchnls=nchnls)
    if output_device is not None:
        server.setOutputDevice(output_device)
    server.boot()
    server.start()
    return server


class Sequencer(Protocol):
    """Anything a `Patch` can start/stop ticking - a `Clock` `Division`, a
    raw pyo `Pattern`, or clock_tick's multi-`Pattern` fan-out."""

    def play(self) -> None: ...
    def stop(self) -> None: ...


@dataclass
class Patch:
    """A step sequencer paired with the audio chain it drives.

    Building a patch only wires up the pyo object graph - nothing is audible
    or ticking until `start()` is called, and nothing keeps running after
    `stop()`.
    """

    sequencer: Sequencer
    voice: PyoObject
    controls: dict[str, Callable[[Any], None]] = field(default_factory=dict)
    volume: float = 1.0
    _output: PyoObject | None = field(default=None, repr=False)
    _fade: SigTo | None = field(default=None, repr=False)
    _volume_control: SigTo | None = field(default=None, repr=False)

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
            raise KeyError(f"Patch has no live parameter named {name!r}") from error
        setter(value)

    def update(self, values: dict[str, Any]) -> Patch:
        """Update several live parameters and preserve runtime state."""
        for name, value in values.items():
            self.set(name, value)
        return self

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
        compressed = Compress(
            boosted, thresh=-1, ratio=10, risetime=0.001, falltime=0.05
        )
        # pyo's stop(wait=...) only delays the hard cutoff, it doesn't fade
        # the signal itself - multiplying by this ramp is what actually
        # brings the level to zero before that cutoff lands, on both this
        # start (from silence) and the next stop() (see below)
        self._fade = SigTo(value=1.0, time=STOP_FADE)
        # mono voices only have one stream, so .out() alone would only reach channel 0
        self._output = (compressed * self._fade).mix(2).out()
        self.sequencer.play()
        return self

    def stop(self) -> Patch:
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
    `hat_patch` doesn't stop the previous Patch - pyo's audio graph keeps
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
