from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, ClassVar, Literal, overload

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.theory.catalog import Catalog, CatalogItem
from pyoscillate.theory.pitch import Note


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

    `scale="cutoff"` is for a frequency swept for brightness (a filter
    cutoff in Hz). The track runs 0-1 and a power curve spends most of it on
    the low end, where each step is an audible change, instead of letting the
    top octave take half the slider. `step` counts track units (0.02 = 50
    ticks), while `minimum`, `maximum` and `default` stay in Hz.
    """

    CUTOFF_CURVE: ClassVar[float] = 4.0

    name: str
    minimum: float
    maximum: float
    step: float
    default: float
    description: str
    help_text: str
    scale: Literal["linear", "note", "cutoff"] = "linear"
    # named choices for a stepped parameter: the value is an index into
    # these, and a UI shows a dropdown instead of a slider
    options: tuple[str, ...] = ()
    # a stable id for each option, in the same order: what a preset stores,
    # so a saved choice survives the catalog being reordered
    option_ids: tuple[str, ...] = ()
    # the category each option sits under, in the same order, so a UI can
    # split a long dropdown by category; empty when the options are ungrouped
    option_categories: tuple[str, ...] = ()

    def to_position(self, value: float) -> float:
        """Where `value` sits on the slider's track."""
        if self.scale == "note":
            return round(Note.freq_to_midi(value) / self.step) * self.step
        if self.scale == "cutoff":
            span = self.maximum - self.minimum
            fraction = min(max((value - self.minimum) / span, 0.0), 1.0)
            return fraction ** (1 / self.CUTOFF_CURVE)
        return value

    def from_position(self, position: float) -> float:
        """The parameter value for a track position, snapped to a tick."""
        if self.scale == "note":
            return Note.midi_to_freq(round(position / self.step) * self.step)
        if self.scale == "cutoff":
            ticked = min(max(round(position / self.step) * self.step, 0.0), 1.0)
            return (
                self.minimum + (self.maximum - self.minimum) * ticked**self.CUTOFF_CURVE
            )
        return position

    def snap(self, value: float) -> float:
        """A stored value (a preset) brought onto the nearest note, clamped to
        the range; cutoff values are only clamped, linear ones pass through."""
        if self.scale == "cutoff":
            return min(max(value, self.minimum), self.maximum)
        if self.scale != "note":
            return value
        lowest, highest = self.to_position(self.minimum), self.to_position(self.maximum)
        return self.from_position(min(max(self.to_position(value), lowest), highest))

    @property
    def divisions(self) -> int:
        if self.scale == "cutoff":
            return max(1, round(1 / self.step))
        span = self.to_position(self.maximum) - self.to_position(self.minimum)
        return max(1, round(span / self.step))

    def format(self, value: float) -> str:
        if self.options:
            return self.options[min(max(int(value), 0), len(self.options) - 1)]
        if self.scale == "note":
            return Note.name(value)
        if self.scale == "cutoff":
            return f"{value:.0f}"
        return f"{value:.{decimal_places(self.step)}f}"


Control = Callable[[Any, float], None]


def noop_control(patch: Any, value: float) -> None:
    """The control of a `Param` that only `build()` or a `live()` signal reads."""


class Param:
    """One patch parameter declared once: its slider contract, its current
    per-instance value, and how that value drives the live graph.

    Used like `@property`, decorating the control itself - the method name
    becomes the parameter name:

        @Param(0.0, 2.0, 0.05, 1.0, "Punch", "...")
        def punch(self, value: float) -> None:
            self.pitch.mul = self.sweep_depth * value

    `self.punch` reads the current value; assigning it stores it and, once
    the patch is built, runs the control. `finish()` runs every control once
    with the current value, so a mapping like `sweep_depth * value` is written
    only here, never again in `build()`. A `Param` with no control is a plain
    value `build()` reads (a `rebuild` parameter, see `rebuild=True`), unless
    `build()` hands it a `SigTo` with `self.live(Patch.param)`, in which case
    assigning it glides that signal. A style subclass changes a field while
    keeping the control with `punch = Kick.punch.replace(default=1.4)`.

    The `Param` object itself is the handle everywhere: racks assign
    `patch.punch = 1.2`, sliders and presets hold the `Param`, and nothing
    looks a parameter up by its string name.

    `sweep=True` lets a patch instance drive the parameter with a bouncing
    low/high sweep instead of a fixed value (see `patches/sweep.py`); it
    needs a live control (or a `live()` signal) and is meaningless for a
    `rebuild` parameter.
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
        scale: Literal["linear", "note", "cutoff"] = "linear",
        rebuild: bool = False,
        sweep: bool = False,
        options: tuple[str, ...] = (),
        option_ids: tuple[str, ...] = (),
        option_categories: tuple[str, ...] = (),
        catalog: type[Catalog] | None = None,
        control: Control = noop_control,
    ) -> None:
        raw_default = default
        if catalog is not None:
            options, option_ids = catalog.labels(), catalog.ids()
            option_categories = catalog.categories()
            minimum, maximum, step = 0, len(options) - 1, 1
            if isinstance(default, CatalogItem):
                default = catalog.index_of(default)
        self._fields: dict[str, Any] = {
            "minimum": minimum,
            "maximum": maximum,
            "step": step,
            "default": default,
            "label": label,
            "help_text": help_text,
            "scale": scale,
            "rebuild": rebuild,
            "sweep": sweep,
            "options": options,
            "option_ids": option_ids,
            "option_categories": option_categories,
        }
        # what `replace` starts from: the arguments as given, so a catalog
        # member default is re-resolved if the catalog is swapped
        self._given: dict[str, Any] = {
            "minimum": minimum,
            "maximum": maximum,
            "step": step,
            "default": raw_default,
            "label": label,
            "help_text": help_text,
            "scale": scale,
            "rebuild": rebuild,
            "sweep": sweep,
            "options": options,
            "option_ids": option_ids,
            "option_categories": option_categories,
            "catalog": catalog,
        }
        self.control = control
        # the catalog a choice parameter's options come from, if any
        self.catalog = catalog
        self.rebuild = rebuild
        # whether each patch instance may sweep this parameter (see `Sweep`)
        self.sweep = sweep
        self.name = ""
        self.spec: SliderSpec
        # the `Param` this one was `replace`d from (itself if never replaced),
        # so a rack control can recognise one parameter across style overrides
        self.origin: Param = self

    def __call__(self, control: Control) -> Param:
        self.control = control
        return self

    def replace(self, **changes: Any) -> Param:
        """A copy with some slider fields changed and the same control."""
        copy = Param(**{**self._given, **changes}, control=self.control)
        copy.origin = self.origin
        return copy

    def __set_name__(self, owner: type[Any], name: str) -> None:
        self.name = name
        fields = dict(self._fields)
        fields.pop("rebuild")
        fields.pop("sweep")
        self.spec = SliderSpec(name, description=fields.pop("label"), **fields)

    @property
    def default(self) -> float:
        return self.spec.default

    def read(self, obj: Any) -> float:
        """This parameter's current value on `obj`."""
        return obj.__dict__[self.name]

    def write(self, obj: Any, value: float) -> None:
        """Assign `value` on `obj` exactly as `obj.<name> = value` does."""
        self.__set__(obj, value)

    @overload
    def __get__(self, obj: None, owner: type[Any] | None = None) -> Param: ...
    @overload
    def __get__(self, obj: object, owner: type[Any] | None = None) -> float: ...
    def __get__(
        self, obj: object | None, owner: type[Any] | None = None
    ) -> Param | float:
        if obj is None:
            return self
        return obj.__dict__[self.name]

    def __set__(self, obj: Any, value: float | CatalogItem) -> None:
        if isinstance(value, CatalogItem):
            if value.id not in self.spec.option_ids:
                raise ValueError(f"{self.name} does not offer {value.id!r}")
            value = self.spec.option_ids.index(value.id)
        obj.__dict__[self.name] = value
        if obj.built:
            obj.apply_param(self, value)


class RateParam(Param):
    """The clocked-patch rate: an integer number of `NoteDivision` steps away
    from `base_division`, valid across `Clock.rate_limits(base_division)`.
    Its control re-spaces the patch's scheduled division."""

    def __init__(self, base_division: NoteDivision, help_text: str) -> None:
        minimum, maximum = Clock.rate_limits(base_division)
        super().__init__(
            minimum, maximum, 1, 0, "Rate", help_text, control=RateParam.reschedule
        )

    @staticmethod
    def reschedule(patch: Any, value: float) -> None:
        patch.reschedule(value)


def rate_param(base_division: NoteDivision, help_text: str) -> Param:
    """The standard "rate" `Param` shared by every clocked patch."""
    return RateParam(base_division, help_text)


def choice_param(
    catalog: type[Catalog],
    default: CatalogItem,
    help_text: str,
    *,
    label: str = "Pattern",
    rebuild: bool = False,
    control: Control = noop_control,
) -> Param:
    """A dropdown `Param` over every member of `catalog`, stored as the
    member's position and persisted as its id. A style picks its own starting
    member with `Voice.phrase.replace(default=Member)`, and assigning a member
    (`self.phrase = Member`) selects it."""
    return Param(
        0,
        0,
        1,
        default,
        label,
        help_text,
        rebuild=rebuild,
        catalog=catalog,
        control=control,
    )
