from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Tempo:
    """Note durations (in seconds) derived from a BPM, shared across patches
    so they all lock to the same grid."""

    bpm: float

    @property
    def sixteenth(self) -> float:
        return 60.0 / self.bpm / 4

    @property
    def eighth(self) -> float:
        return self.sixteenth * 2

    @property
    def fourth(self) -> float:
        return self.eighth * 2

    @property
    def bar(self) -> float:
        return self.sixteenth * 16
