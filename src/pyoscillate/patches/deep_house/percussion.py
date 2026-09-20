"""Accent percussion voices for the Deep House project."""

from collections.abc import Callable

from ipywidgets import VBox
from pyo.lib.filters import Biquad
from pyo.lib.generators import Noise, Sine
from pyo.lib.tables import CosTable
from pyo.lib.triggers import Trig, TrigEnv

from pyoscillate.clock import SIXTEENTH, Clock
from pyoscillate.patches.base import Patch, PatchRack
from pyoscillate.patches.presets import PresetController
from pyoscillate.patches.widgets import SliderSpec, patch_widget
from pyoscillate.tempo import Tempo

PARAMETERS = (
    SliderSpec("level", 0.02, 0.6, 0.01, 0.18, "Level", "Percussion burst level."),
    SliderSpec("tone", 180, 4000, 20, 1100, "Tone", "Percussion resonant frequency."),
)
PATTERNS = {
    "clap": {4, 12},
    "rim": {3, 7, 11, 15},
    "conga": {3, 6, 9, 11, 14},
}
DURATIONS = {"clap": 0.16, "rim": 0.07, "conga": 0.19}
VOLUME_DEFAULT = 0.28


def build(
    tempo: Tempo, clock: Clock, style: str, level: float = 0.18, tone: float = 1100
) -> Patch:
    """Build claps, rims, or conga-like resonance from the same rhythmic layer."""
    trigger = Trig()
    envelope = TrigEnv(
        trigger, CosTable([(0, 0), (30, 1), (8191, 0)]), dur=DURATIONS[style], mul=level
    )
    source = Noise() if style == "clap" else Sine(freq=tone)
    voice = Biquad(
        source * envelope,
        freq=tone,
        q=5 if style != "clap" else 1.1,
        type=2 if style != "clap" else 1,
    )
    state = {"step": 0}

    def next_step() -> None:
        step = state["step"] % 16
        if step in PATTERNS[style]:
            trigger.play()
        state["step"] += 1

    return Patch(
        sequencer=clock.subscribe(SIXTEENTH, next_step),
        voice=voice,
        controls={
            "level": lambda value: setattr(envelope, "mul", value),
            "tone": lambda value: setattr(voice, "freq", value),
        },
    )


def make_builder(style: str) -> Callable[..., Patch]:
    """Return a builder with one percussion style fixed for a rack entry."""
    return lambda tempo, clock, **values: build(tempo, clock, style, **values)


def widget(
    rack: PatchRack,
    tempo: Tempo,
    clock: Clock,
    controller: PresetController | None = None,
    style: str = "clap",
) -> VBox:
    """Create controls for one percussion style."""
    return patch_widget(
        rack,
        f"percussion_{style}",
        make_builder(style),
        PARAMETERS,
        controller=controller,
        volume_default=VOLUME_DEFAULT,
        build_kwargs={"tempo": tempo, "clock": clock},
    )