from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.patches.utility.notes.notes import (
    freq_to_midi,
    midi_to_freq,
    note_name,
)


def decimal_places(step: float) -> int:
    return max(0, len(str(step).partition(".")[2].rstrip("0")))


@dataclass(frozen=True)
class PyoParamRef:
    owner: type[Any]
    name: str


@dataclass(frozen=True)
class SliderSpec:
    """One slider: `minimum`, `maximum` and `default` are always in the
    parameter's own unit, the value the patch's `build()` and controls see.

    `scale="note"` is for pitch parameters in Hz. The slider's ticks sit on
    equal-tempered notes instead of evenly spaced Hz, `step` counts
    semitones, and every value it produces is an in-tune note frequency, so
    a Register slider can't leave a patch out of tune with the rest of the
    rack. `minimum`, `maximum` and `default` should themselves be notes.
    """

    name: str
    minimum: float
    maximum: float
    step: float
    default: float
    description: str
    help_text: str
    pyo_refs: tuple[PyoParamRef, ...] = ()
    scale: Literal["linear", "note"] = "linear"

    def to_position(self, value: float) -> float:
        """Where `value` sits on the slider's track."""
        if self.scale == "note":
            return round(freq_to_midi(value) / self.step) * self.step
        return value

    def from_position(self, position: float) -> float:
        """The parameter value for a track position, snapped to a tick."""
        if self.scale == "note":
            return midi_to_freq(round(position / self.step) * self.step)
        return position

    def snap(self, value: float) -> float:
        """A stored value (a preset) brought onto the nearest note, clamped to
        the range; linear values pass through unchanged."""
        if self.scale != "note":
            return value
        lowest, highest = self.to_position(self.minimum), self.to_position(self.maximum)
        return self.from_position(min(max(self.to_position(value), lowest), highest))

    @property
    def divisions(self) -> int:
        span = self.to_position(self.maximum) - self.to_position(self.minimum)
        return max(1, round(span / self.step))

    def format(self, value: float) -> str:
        if self.scale == "note":
            return note_name(value)
        return f"{value:.{decimal_places(self.step)}f}"


def rate_slider(base_division: NoteDivision, help_text: str) -> SliderSpec:
    """The standard "rate" `SliderSpec` shared by every clocked patch: an
    integer number of `NoteDivision` steps away from `base_division`, valid
    across `Clock.rate_limits(base_division)`. Each patch still supplies its
    own `help_text`, since the perceptual description of what the rate does
    is family-specific.
    """
    minimum, maximum = Clock.rate_limits(base_division)
    return SliderSpec("rate", minimum, maximum, 1, 0, "Rate", help_text)
