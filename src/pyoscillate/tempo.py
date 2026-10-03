from __future__ import annotations

from dataclasses import dataclass


@dataclass(eq=False)
class Tempo:
    """Note durations (in seconds) derived from a BPM, shared across patches
    so they all lock to the same grid.

    Mutable on purpose: the rack changes `bpm` while it plays, so anything
    that needs a note length reads it from here each time rather than copying
    a number. Patches register those derived values with `Patch.sync()` so
    `Patch.retempo()` can recompute them after `set_bpm()`.
    """

    bpm: float

    def set_bpm(self, bpm: float) -> None:
        if bpm <= 0:
            raise ValueError(f"bpm must be positive, got {bpm}")
        self.bpm = bpm

    @property
    def thirtysecond(self) -> float:
        return 60.0 / self.bpm / 8

    @property
    def sixteenth(self) -> float:
        return self.thirtysecond * 2

    @property
    def eighth(self) -> float:
        return self.sixteenth * 2

    @property
    def fourth(self) -> float:
        return self.eighth * 2

    @property
    def bar(self) -> float:
        return self.sixteenth * 16
