# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.musical.chord.chord style=velvet
#   style: velvet | organ | shimmer
"""Offbeat chord-stab voices."""

from collections.abc import Callable

from pyo.lib.effects import Chorus, Freeverb
from pyo.lib.filters import Biquad
from pyo.lib.tableprocess import Osc
from pyo.lib.tables import CosTable, HarmTable, SawTable
from pyo.lib.triggers import Trig, TrigEnv

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import Patch
from pyoscillate.patches.params import SliderSpec
from pyoscillate.tempo import Tempo

BASE_DIVISION = NoteDivision.SIXTEENTH

PARAMETERS = (
    SliderSpec(
        "octave",
        -1,
        1,
        1,
        0,
        "Register",
        "Moves the chord stabs down an octave for a darker, lower bed or up an octave to "
        "sit clearer above the bass; the chords always follow the rack's key and progression.",
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
# i-iv-bVII-v as parallel minor-seventh stabs, one chord per bar - used
# only when the patch runs outside a rack that shares its own `Harmony`
FALLBACK_HARMONY = Harmony(progression=(0, 5, 10, 7))
INTERVALS = (0, 3, 7, 10)
# every chord root snaps to the octave nearest this, around D3
REGISTER_CENTRE = 146
VOLUME_DEFAULT = 0.4


def build(
    tempo: Tempo,
    clock: Clock,
    style: str,
    octave: float = 0,
    brightness: float = 1500,
    rate: float = 0,
    harmony: Harmony | None = None,
) -> Patch:
    """Build an offbeat minor-seventh chord stab from four explicit voices.

    Each stab voices the chord `harmony` says is sounding in the current bar,
    so the progression stays locked to the bass and tom whatever this
    patch's rate or start time."""
    harmony = harmony or FALLBACK_HARMONY
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
        Osc(
            table,
            freq=harmony.chord_freq(REGISTER_CENTRE, clock.bar_index)
            * 2 ** (octave + interval / 12),
            mul=amplitude,
        )
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
    state = {"step": 0, "octave": octave}

    def next_step() -> None:
        step = state["step"] % 16
        if step % 4 == 2:
            chord_root = (
                harmony.chord_freq(REGISTER_CENTRE, clock.bar_index)
                * 2 ** state["octave"]
            )
            for oscillator, interval in zip(voices, INTERVALS, strict=True):
                oscillator.freq = chord_root * 2 ** (interval / 12)
            trigger.play()
        state["step"] += 1

    division = clock.subscribe(clock.ticks_for_rate(BASE_DIVISION, rate), next_step)
    return Patch(
        sequencer=division,
        voice=voice,
        controls={
            "octave": lambda value: state.update(octave=value),
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
