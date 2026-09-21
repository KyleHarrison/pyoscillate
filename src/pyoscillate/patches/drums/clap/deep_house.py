"""Clap voice for the Deep House project."""

from ipywidgets import VBox
from pyo.lib.filters import Biquad
from pyo.lib.generators import Noise
from pyo.lib.tables import CosTable
from pyo.lib.triggers import Trig, TrigEnv

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.patches.base import Patch, PatchRack
from pyoscillate.patches.presets import PresetController
from pyoscillate.patches.widgets import SliderSpec, patch_widget
from pyoscillate.tempo import Tempo

BASE_DIVISION = NoteDivision.SIXTEENTH

PARAMETERS = (
    SliderSpec(
        "level",
        0.02,
        0.6,
        0.01,
        0.18,
        "Presence",
        "Sets how loud and upfront the clap accent sits in the mix.",
    ),
    SliderSpec(
        "tone",
        180,
        4000,
        20,
        1100,
        "Brightness",
        "Moves the clap from fuller and softer to thinner and sharper.",
    ),
    SliderSpec(
        "rate",
        -1,
        2,
        1,
        0,
        "Rate",
        "Steps the clap pattern to a slower or faster bar division - -1 "
        "drops to an 8th note (half speed), 0 is the default 16th note, "
        "+1 rises to a 32nd note (double speed).",
    ),
)
PATTERN = {4, 12}
DURATION = 0.16
VOLUME_DEFAULT = 0.28


def _steps_for_rate(clock: Clock, rate: float) -> int:
    """Raw ticks for a `rate` slider step, always a real `NoteDivision`."""
    note_division = NoteDivision(BASE_DIVISION * (2 ** round(rate)))
    return clock.ticks(note_division)


def build(
    tempo: Tempo,
    clock: Clock,
    level: float = 0.18,
    tone: float = 1100,
    rate: float = 0,
) -> Patch:
    """Build a bright, filtered noise clap on beats two and four."""
    trigger = Trig()
    envelope_table = CosTable([(0, 0), (30, 1), (8191, 0)])
    envelope = TrigEnv(trigger, envelope_table, dur=DURATION, mul=level)
    noise = Noise()
    source = noise * envelope
    voice = Biquad(source, freq=tone, q=1.1, type=1)
    state = {"step": 0}

    def next_step() -> None:
        if state["step"] % 16 in PATTERN:
            trigger.play()
        state["step"] += 1

    division = clock.subscribe(_steps_for_rate(clock, rate), next_step)

    def set_rate(value: float) -> None:
        division.steps = _steps_for_rate(clock, value)

    return Patch(
        sequencer=division,
        voice=voice,
        controls={
            "level": lambda value: setattr(envelope, "mul", value),
            "tone": lambda value: setattr(voice, "freq", value),
            "rate": set_rate,
        },
        resources=(trigger, envelope_table, envelope, noise, source),
    )


def widget(
    rack: PatchRack,
    tempo: Tempo,
    clock: Clock,
    controller: PresetController | None = None,
) -> VBox:
    """Create controls for the clap voice."""
    return patch_widget(
        rack,
        "clap",
        build,
        PARAMETERS,
        controller=controller,
        volume_default=VOLUME_DEFAULT,
        build_kwargs={"tempo": tempo, "clock": clock},
    )
