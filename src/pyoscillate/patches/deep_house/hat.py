"""Hi-hat voices for the Deep House project."""

from collections.abc import Callable

from ipywidgets import VBox
from pyo.lib.filters import ButHP
from pyo.lib.generators import Noise
from pyo.lib.tables import CosTable
from pyo.lib.triggers import Trig, TrigEnv

from pyoscillate.clock import SIXTEENTH, Clock
from pyoscillate.patches.base import Patch, PatchRack
from pyoscillate.patches.presets import PresetController
from pyoscillate.patches.widgets import SliderSpec, patch_widget
from pyoscillate.tempo import Tempo

PARAMETERS = (
    SliderSpec("level", 0.02, 0.5, 0.01, 0.14, "Presence", "Sets how loud and upfront the hat pattern sits in the mix."),
    SliderSpec("cutoff", 3500, 14000, 100, 9000, "Brightness", "Moves the hat from fuller and closer to a hiss (lower) to thinner and airier (higher)."),
)
PATTERNS = {
    "crisp": {2, 6, 10, 14},
    "open": {2, 6, 10, 14, 15},
    "shuffle": {2, 5, 6, 10, 13, 14},
}
DURATIONS = {"crisp": 0.07, "open": 0.22, "shuffle": 0.11}
VOLUME_DEFAULT = 0.25


def build(
    tempo: Tempo, clock: Clock, style: str, level: float = 0.14, cutoff: float = 9000
) -> Patch:
    """Build a style-specific, grid-locked hat pattern."""
    trigger = Trig()
    envelope = TrigEnv(
        trigger, CosTable([(0, 0), (35, 1), (8191, 0)]), dur=DURATIONS[style], mul=level
    )
    voice = ButHP(Noise() * envelope, freq=cutoff)
    state = {"step": 0}

    def next_step() -> None:
        step = state["step"] % 16
        if step in PATTERNS[style]:
            envelope.mul = level if step % 4 == 2 else level * 0.66
            trigger.play()
        state["step"] += 1

    return Patch(
        sequencer=clock.subscribe(SIXTEENTH, next_step),
        voice=voice,
        controls={
            "level": lambda value: setattr(envelope, "mul", value),
            "cutoff": lambda value: setattr(voice, "freq", value),
        },
    )


def make_builder(style: str) -> Callable[..., Patch]:
    """Return a builder with one hat style fixed for a rack entry."""
    return lambda tempo, clock, **values: build(tempo, clock, style, **values)


def widget(
    rack: PatchRack,
    tempo: Tempo,
    clock: Clock,
    controller: PresetController | None = None,
    style: str = "crisp",
) -> VBox:
    """Create controls for one hat style."""
    return patch_widget(
        rack,
        f"hat_{style}",
        make_builder(style),
        PARAMETERS,
        controller=controller,
        volume_default=VOLUME_DEFAULT,
        build_kwargs={"tempo": tempo, "clock": clock},
    )