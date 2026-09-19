from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from pyo import PyoObject


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

    def start(self) -> Patch:
        self.voice.out()
        self.sequencer.play()
        return self

    def stop(self) -> Patch:
        self.sequencer.stop()
        self.voice.stop()
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

    def start(self, name: str, patch: Patch) -> Patch:
        self.stop(name)
        self._patches[name] = patch
        return patch.start()

    def stop(self, name: str) -> None:
        existing = self._patches.pop(name, None)
        if existing is not None:
            existing.stop()

    def stop_all(self) -> None:
        for name in list(self._patches):
            self.stop(name)
