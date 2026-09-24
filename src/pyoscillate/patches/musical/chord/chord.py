"""Offbeat chord-stab voices."""

from collections.abc import Callable

from pyo.lib.effects import Chorus, Freeverb
from pyo.lib.filters import Biquad
from pyo.lib.tableprocess import Osc
from pyo.lib.tables import CosTable, HarmTable, SawTable
from pyo.lib.triggers import Trig, TrigEnv

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.patches.base import Patch
from pyoscillate.patches.params import SliderSpec
from pyoscillate.tempo import Tempo

BASE_DIVISION = NoteDivision.SIXTEENTH

PARAMETERS = (
    SliderSpec(
        "root_freq",
        90,
        220,
        1,
        146,
        "Register",
        "Shifts the chord stab up or down in pitch relative to the bass and kick.",
    ),
    SliderSpec(
        "brightness",
        300,
        5000,
        50,
        1500,
        "Brightness",
        "Opens or closes the stab's tone, from a dark, rounded voicing to a brighter, more cutting one.",
    ),
    SliderSpec(
        "rate",
        Clock.rate_limits(BASE_DIVISION)[0],
        Clock.rate_limits(BASE_DIVISION)[1],
        1,
        0,
        "Rate",
        "Halves or doubles the chord-stab pattern speed for each step away from its 16th-note grid.",
    ),
)
ROOTS = [0, 5, 10, 7]
INTERVALS = (0, 3, 7, 10)
VOLUME_DEFAULT = 0.4


def build(
    tempo: Tempo,
    clock: Clock,
    style: str,
    root_freq: float = 146,
    brightness: float = 1500,
    rate: float = 0,
) -> Patch:
    """Build an offbeat minor-seventh chord stab from four explicit voices."""
    profiles = {
        "velvet": (lambda: HarmTable([1, 0.25, 0.12]), 0.34, 0.42),
        "organ": (lambda: HarmTable([1, 0.7, 0.4, 0.2]), 0.22, 0.2),
        "shimmer": (lambda: SawTable(order=12), 0.42, 0.58),
    }
    table_factory, duration, wet = profiles[style]
    table = table_factory()
    trigger = Trig()
    envelope_table = CosTable([(0, 0), (200, 1), (2500, 0.55), (8191, 0)])
    envelope = TrigEnv(trigger, envelope_table, dur=duration)
    amplitude = envelope * 0.19
    voices = [
        Osc(table, freq=root_freq * 2 ** (interval / 12), mul=amplitude)
        for interval in INTERVALS
    ]
    source = sum(voices)
    filter_voice = Biquad(source, freq=brightness, q=1.2, type=0)
    voice = filter_voice
    chorus = None
    if style == "shimmer":
        chorus = Chorus(voice, depth=1.2, feedback=0.15, bal=0.28)
        voice = chorus
    voice = Freeverb(voice, size=0.72, damp=0.45, bal=wet)
    state = {"step": 0, "root": root_freq}

    def next_step() -> None:
        step = state["step"] % 16
        if step % 4 == 2:
            chord_root = state["root"] * 2 ** (ROOTS[(step // 4) % 4] / 12)
            for oscillator, interval in zip(voices, INTERVALS, strict=True):
                oscillator.freq = chord_root * 2 ** (interval / 12)
            trigger.play()
        state["step"] += 1

    division = clock.subscribe(clock.ticks_for_rate(BASE_DIVISION, rate), next_step)
    return Patch(
        sequencer=division,
        voice=voice,
        controls={
            "root_freq": lambda value: state.update(root=value),
            "brightness": lambda value: setattr(filter_voice, "freq", value),
            "rate": lambda value: setattr(
                division, "steps", clock.ticks_for_rate(BASE_DIVISION, value)
            ),
        },
        resources=(
            table,
            trigger,
            envelope_table,
            envelope,
            amplitude,
            *voices,
            source,
            filter_voice,
            chorus,
        ),
    )


def make_builder(style: str) -> Callable[..., Patch]:
    """Return a builder with one chord style fixed for a rack entry."""
    return lambda tempo, clock, **values: build(tempo, clock, style, **values)
