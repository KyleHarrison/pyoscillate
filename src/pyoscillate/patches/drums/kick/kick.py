# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.drums.kick.kick style=round
#   style: round | punch | soft
"""Four-on-the-floor kick voices.

Each hit restarts a sine body at a zero crossing, so the impact starts at full
amplitude without a phase click. An exponential pitch drop gives the attack
its gesture, an exponential amplitude decay sets the body length, a short
noise burst clarifies the transient, and gentle saturation adds density.
"""

from collections.abc import Callable

from pyo.lib.effects import Disto
from pyo.lib.generators import Noise, Sine
from pyo.lib.tables import ExpTable
from pyo.lib.triggers import Trig, TrigEnv

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.patches.base import Patch
from pyoscillate.patches.params import SliderSpec
from pyoscillate.tempo import Tempo

BASE_DIVISION = NoteDivision.QUARTER

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
    SliderSpec(
        "punch",
        0.0,
        2.0,
        0.05,
        1.0,
        "Punch",
        "Depth of the downward pitch drop at the start of each hit; more gives a sharper, more pronounced "
        "attack, too much starts to sound like a tom or zap, none leaves a pure low thud.",
    ),
    SliderSpec(
        "length",
        0.5,
        2.0,
        0.05,
        1.0,
        "Length",
        "Stretches or shortens the body; shorter is tight and dry and leaves room for the bass, longer is "
        "boomier and more 808-like but can mask the bassline.",
    ),
    SliderSpec(
        "click",
        0.0,
        2.0,
        0.05,
        1.0,
        "Click",
        "Level of the short noise transient on the attack; more adds snap and definition, less sounds "
        "rounder and softer.",
    ),
    SliderSpec(
        "rate",
        Clock.rate_limits(BASE_DIVISION)[0],
        Clock.rate_limits(BASE_DIVISION)[1],
        1,
        0,
        "Rate",
        "Halves or doubles the kick pattern speed for each step away from the four-on-the-floor default.",
    ),
)
# settled body pitch (Hz), pitch-drop depth (Hz above body), pitch-drop time
# (s), body decay (s), transient level
PROFILES = {
    "round": (50.0, 80.0, 0.05, 0.27, 0.12),
    "punch": (54.0, 140.0, 0.035, 0.2, 0.28),
    "soft": (46.0, 50.0, 0.07, 0.37, 0.05),
}
# exponent of the amplitude and pitch decay curves - higher values give the
# fast-drop, long-tail shape of an analogue drum envelope; the body stays
# moderate so the kick keeps its weight
BODY_CURVE = 2.5
PITCH_CURVE = 6
CLICK_DURATION = 0.012
VOLUME_DEFAULT = 0.8


def build(
    tempo: Tempo,
    clock: Clock,
    style: str,
    level: float = 0.62,
    drive: float = 0.12,
    punch: float = 1.0,
    length: float = 1.0,
    click: float = 1.0,
    rate: float = 0,
) -> Patch:
    """Build a four-on-the-floor kick in the requested style."""
    body_freq, sweep_depth, sweep_time, decay, click_level = PROFILES[style]
    trigger = Trig()

    pitch_table = ExpTable([(0, 1), (8191, 0)], exp=PITCH_CURVE)
    pitch = TrigEnv(
        trigger, pitch_table, dur=sweep_time, mul=sweep_depth * punch, add=body_freq
    )
    body = Sine(freq=pitch)
    envelope_table = ExpTable([(0, 1), (8191, 0)], exp=BODY_CURVE)
    envelope = TrigEnv(trigger, envelope_table, dur=decay * length, mul=level)
    body_signal = body * envelope

    noise = Noise()
    click_table = ExpTable([(0, 1), (8191, 0)], exp=PITCH_CURVE)
    click_env = TrigEnv(
        trigger, click_table, dur=CLICK_DURATION, mul=click_level * click
    )
    click_signal = noise * click_env

    source = body_signal + click_signal
    voice = Disto(source, drive=drive, slope=0.85)

    def strike() -> None:
        # restart the sine at phase zero so the full-level attack starts on a
        # zero crossing instead of wherever the oscillator last stopped
        body.reset()
        trigger.play()

    division = clock.subscribe(clock.ticks_for_rate(BASE_DIVISION, rate), strike)
    return Patch(
        sequencer=division,
        voice=voice,
        controls={
            "level": lambda value: setattr(envelope, "mul", value),
            "drive": lambda value: setattr(voice, "drive", value),
            "punch": lambda value: setattr(pitch, "mul", sweep_depth * value),
            "length": lambda value: setattr(envelope, "dur", decay * value),
            "click": lambda value: setattr(click_env, "mul", click_level * value),
            "rate": lambda value: setattr(
                division, "steps", clock.ticks_for_rate(BASE_DIVISION, value)
            ),
        },
        resources=(
            trigger,
            pitch_table,
            pitch,
            body,
            envelope_table,
            envelope,
            body_signal,
            noise,
            click_table,
            click_env,
            click_signal,
            source,
        ),
    )


def make_builder(style: str) -> Callable[..., Patch]:
    """Return a builder with one kick style fixed for a rack entry."""
    return lambda tempo, clock, **values: build(tempo, clock, style, **values)
