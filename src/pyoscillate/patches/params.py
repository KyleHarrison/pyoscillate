from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal, overload

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.patches.utility.notes.notes import (
    freq_to_midi,
    midi_to_freq,
    note_name,
)


def decimal_places(step: float) -> int:
    return max(0, len(str(step).partition(".")[2].rstrip("0")))


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


Control = Callable[[Any, float], None]


class Param:
    """One patch parameter declared once: its slider contract, its current
    per-instance value, and how that value drives the live graph.

    Used like `@property`, decorating the control itself - the method name
    becomes the parameter name:

        @Param(0.0, 2.0, 0.05, 1.0, "Punch", "...")
        def punch(self, value: float) -> None:
            self.pitch.mul = self.sweep_depth * value

    `self.punch` reads the current value; assigning it (or `Patch.set`)
    stores it and, once the patch is built, runs the control. `finish()`
    runs every control once with the current value, so a mapping like
    `sweep_depth * value` is written only here, never again in `build()`.
    A `Param` with no control is a plain value `build()` reads (a
    `rebuild_parameters` name). A style subclass changes a field while
    keeping the control with `punch = Kick.punch.replace(default=1.4)`.
    """

    def __init__(
        self,
        minimum: float,
        maximum: float,
        step: float,
        default: float,
        label: str,
        help_text: str,
        *,
        scale: Literal["linear", "note"] = "linear",
        control: Control | None = None,
    ) -> None:
        self._fields: dict[str, Any] = {
            "minimum": minimum,
            "maximum": maximum,
            "step": step,
            "default": default,
            "label": label,
            "help_text": help_text,
            "scale": scale,
        }
        self.control = control
        self.name = ""
        self.spec: SliderSpec

    def __call__(self, control: Control) -> Param:
        self.control = control
        return self

    def replace(self, **changes: Any) -> Param:
        """A copy with some slider fields changed and the same control."""
        return Param(**{**self._fields, **changes}, control=self.control)

    def __set_name__(self, owner: type[Any], name: str) -> None:
        self.name = name
        fields = dict(self._fields)
        self.spec = SliderSpec(name, description=fields.pop("label"), **fields)

    @overload
    def __get__(self, obj: None, owner: type[Any] | None = None) -> Param: ...
    @overload
    def __get__(self, obj: object, owner: type[Any] | None = None) -> float: ...
    def __get__(self, obj: object | None, owner: type[Any] | None = None) -> Param | float:
        if obj is None:
            return self
        return obj.__dict__[self.name]

    def __set__(self, obj: Any, value: float) -> None:
        obj.__dict__[self.name] = value
        if self.control is not None and obj._built:
            self.control(obj, value)


def rate_param(base_division: NoteDivision, help_text: str) -> Param:
    """`Param` form of `rate_slider`, bound to `GatedVoice.reschedule`."""
    minimum, maximum = Clock.rate_limits(base_division)
    return Param(
        minimum,
        maximum,
        1,
        0,
        "Rate",
        help_text,
        control=lambda patch, value: patch.reschedule(value),
    )


def rate_slider(base_division: NoteDivision, help_text: str) -> SliderSpec:
    """The standard "rate" `SliderSpec` shared by every clocked patch: an
    integer number of `NoteDivision` steps away from `base_division`, valid
    across `Clock.rate_limits(base_division)`. Each patch still supplies its
    own `help_text`, since the perceptual description of what the rate does
    is family-specific.
    """
    minimum, maximum = Clock.rate_limits(base_division)
    return SliderSpec("rate", minimum, maximum, 1, 0, "Rate", help_text)
