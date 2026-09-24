"""Rim and conga-like accent percussion voices.

Both styles share one construction: a sine body that bends slightly down in
pitch as it strikes, plus a short noise transient rung through a band-pass
tuned relative to the body. The rim keeps the body very short and the
transient bright and woody; the conga uses a lower, longer body with only a
soft touch of transient, a warmer answer to the kick.
"""

from collections.abc import Callable

from pyo.lib._core import Sig
from pyo.lib.filters import Biquad
from pyo.lib.generators import Noise, Sine
from pyo.lib.tables import ExpTable
from pyo.lib.triggers import Trig, TrigEnv

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.patches.base import Patch
from pyoscillate.patches.params import SliderSpec
from pyoscillate.patches.utility.notes import notes
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
        "Sets how loud and upfront the percussion accent sits in the mix.",
    ),
    SliderSpec(
        "tune",
        -12,
        12,
        1,
        0,
        "Pitch",
        "Retunes the accent in semitones; lower is deeper and woodier, higher is thinner and sharper.",
    ),
    SliderSpec(
        "length",
        0.5,
        2.0,
        0.05,
        1.0,
        "Length",
        "Shortens the accent toward a dry, clipped tick or lets it ring out into a rounder, more resonant tone.",
    ),
    SliderSpec(
        "click",
        0.0,
        2.0,
        0.05,
        1.0,
        "Attack",
        "Level of the woody transient on each hit; more gives a sharper, clickier strike, less leaves a "
        "softer, purely tonal hit.",
    ),
    SliderSpec(
        "rate",
        Clock.rate_limits(BASE_DIVISION)[0],
        Clock.rate_limits(BASE_DIVISION)[1],
        1,
        0,
        "Rate",
        "Halves or doubles the accent pattern speed for each step away from its 16th-note grid.",
    ),
)
PATTERNS = {
    "rim": {3, 7, 11, 15},
    "conga": {3, 6, 9, 11, 14},
}
# body pitch (Hz), pitch bend (fraction above body at the strike), bend time
# (s), body decay (s), transient level, transient pitch (ratio to body),
# transient resonance
PROFILES = {
    "rim": (1100.0, 0.12, 0.008, 0.07, 0.9, 1.6, 6.0),
    "conga": (notes.A3, 0.2, 0.03, 0.28, 0.2, 4.0, 3.0),
}
DECAY_CURVE = 3
BEND_CURVE = 6
CLICK_DURATION = 0.008
VOLUME_DEFAULT = 0.28


def _ratio(semitones: float) -> float:
    return 2 ** (semitones / 12)


def build(
    tempo: Tempo,
    clock: Clock,
    style: str,
    level: float = 0.18,
    tune: float = 0,
    length: float = 1.0,
    click: float = 1.0,
    rate: float = 0,
) -> Patch:
    """Build a rim-click or conga-like accent from a bent sine body and transient."""
    base_freq, bend_depth, bend_time, decay, click_level, click_ratio, click_q = (
        PROFILES[style]
    )
    trigger = Trig()
    tuning = Sig(_ratio(tune))
    body_freq = tuning * base_freq

    bend_table = ExpTable([(0, 1), (8191, 0)], exp=BEND_CURVE)
    bend = TrigEnv(trigger, bend_table, dur=bend_time, mul=bend_depth, add=1)
    pitch = body_freq * bend
    body = Sine(freq=pitch)
    envelope_table = ExpTable([(0, 1), (8191, 0)], exp=DECAY_CURVE)
    envelope = TrigEnv(trigger, envelope_table, dur=decay * length, mul=level)
    body_signal = body * envelope

    noise = Noise()
    click_table = ExpTable([(0, 1), (8191, 0)], exp=BEND_CURVE)
    click_env = TrigEnv(
        trigger, click_table, dur=CLICK_DURATION, mul=click_level * click * level
    )
    click_burst = noise * click_env
    click_freq = body_freq * click_ratio
    click_signal = Biquad(click_burst, freq=click_freq, q=click_q, type=2)

    voice = body_signal + click_signal
    state = {"step": 0, "level": level, "click": click}

    def next_step() -> None:
        step = state["step"] % 16
        if step in PATTERNS[style]:
            # restart the body on a zero crossing so the immediate attack
            # doesn't click wherever the oscillator last stopped
            body.reset()
            trigger.play()
        state["step"] += 1

    def set_level(value: float) -> None:
        state["level"] = value
        envelope.mul = value
        click_env.mul = click_level * state["click"] * value

    def set_click(value: float) -> None:
        state["click"] = value
        click_env.mul = click_level * value * state["level"]

    division = clock.subscribe(clock.ticks_for_rate(BASE_DIVISION, rate), next_step)
    return Patch(
        sequencer=division,
        voice=voice,
        controls={
            "level": set_level,
            "tune": lambda value: setattr(tuning, "value", _ratio(value)),
            "length": lambda value: setattr(envelope, "dur", decay * value),
            "click": set_click,
            "rate": lambda value: setattr(
                division, "steps", clock.ticks_for_rate(BASE_DIVISION, value)
            ),
        },
        resources=(
            trigger,
            tuning,
            body_freq,
            bend_table,
            bend,
            pitch,
            body,
            envelope_table,
            envelope,
            body_signal,
            noise,
            click_table,
            click_env,
            click_burst,
            click_freq,
            click_signal,
        ),
    )


def make_builder(style: str) -> Callable[..., Patch]:
    """Return a builder with one percussion style fixed for a rack entry."""
    return lambda tempo, clock, **values: build(tempo, clock, style, **values)
