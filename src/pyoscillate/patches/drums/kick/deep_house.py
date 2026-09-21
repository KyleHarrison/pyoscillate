"""Four-on-the-floor kick voices for the Deep House project."""

from collections.abc import Callable

from ipywidgets import VBox
from pyo.lib.effects import Disto
from pyo.lib.generators import Noise, Sine
from pyo.lib.tables import CosTable
from pyo.lib.triggers import Trig, TrigEnv, TrigLinseg

from pyoscillate.clock import Clock
from pyoscillate.patches.base import Patch, PatchRack
from pyoscillate.patches.presets import PresetController
from pyoscillate.patches.widgets import SliderSpec, patch_widget
from pyoscillate.tempo import Tempo

PARAMETERS = (
    SliderSpec(
        "level",
        0.1,
        1.0,
        0.05,
        0.62,
        "Body",
        "Controls the fullness and weight of the kick's low end.",
    ),
    SliderSpec(
        "drive",
        0.0,
        0.8,
        0.05,
        0.12,
        "Grit",
        "Adds soft saturation warmth and edge; higher pushes the kick toward a grittier, more aggressive thump.",
    ),
)
PROFILES = {
    "round": (118.0, 0.24, 0.16),
    "punch": (168.0, 0.18, 0.28),
    "soft": (92.0, 0.34, 0.07),
}
VOLUME_DEFAULT = 0.8


def build(
    tempo: Tempo, clock: Clock, style: str, level: float = 0.62, drive: float = 0.12
) -> Patch:
    """Build a four-on-the-floor kick in the requested deep-house style."""
    pitch_start, decay, click = PROFILES[style]
    trigger = Trig()
    pitch = TrigLinseg(trigger, [(0, pitch_start), (0.055, 52), (decay, 48)])
    body = Sine(freq=pitch)
    envelope_table = CosTable([(0, 0), (45, 1), (8191, 0)])
    envelope = TrigEnv(trigger, envelope_table, dur=decay, mul=level)
    noise = Noise()
    click_table = CosTable([(0, 0), (8, 1), (420, 0)])
    click_env = TrigEnv(trigger, click_table, dur=0.035, mul=click)
    body_signal = body * envelope
    click_signal = noise * click_env
    source = body_signal + click_signal
    voice = Disto(source, drive=drive, slope=0.85)
    return Patch(
        sequencer=clock.subscribe(clock.fourth, trigger.play),
        voice=voice,
        controls={
            "level": lambda value: setattr(envelope, "mul", value),
            "drive": lambda value: setattr(voice, "drive", value),
        },
        resources=(
            trigger,
            pitch,
            body,
            envelope_table,
            envelope,
            noise,
            click_table,
            click_env,
            body_signal,
            click_signal,
            source,
        ),
    )


def make_builder(style: str) -> Callable[..., Patch]:
    """Return a builder with one kick style fixed for a rack entry."""
    return lambda tempo, clock, **values: build(tempo, clock, style, **values)


def widget(
    rack: PatchRack,
    tempo: Tempo,
    clock: Clock,
    controller: PresetController | None = None,
    style: str = "round",
) -> VBox:
    """Create controls for one kick style."""
    return patch_widget(
        rack,
        f"kick_{style}",
        make_builder(style),
        PARAMETERS,
        controller=controller,
        volume_default=VOLUME_DEFAULT,
        build_kwargs={"tempo": tempo, "clock": clock},
    )
