from __future__ import annotations

from dataclasses import dataclass

from pyo import PyoObject
from pyo.lib.pattern import Pattern


@dataclass
class Patch:
    """A step sequencer paired with the audio chain it drives.

    Building a patch only wires up the pyo object graph - nothing is audible
    or ticking until `start()` is called, and nothing keeps running after
    `stop()`.
    """

    sequencer: Pattern
    voice: PyoObject

    def start(self) -> Patch:
        self.voice.out()
        self.sequencer.play()
        return self

    def stop(self) -> Patch:
        self.sequencer.stop()
        self.voice.stop()
        return self
