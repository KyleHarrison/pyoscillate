# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.drums.snare.snare
"""Tone-and-rattle snare voice.

Two layers share one trigger: a short sine body a little above the kick's
register, with a modest downward pitch bend, and a louder high-passed noise
rattle whose exponential tail runs from a dry crack to a small-room wash. It
sits on the backbeat under the clap, with a ghost note that swings into the
next bar.
"""

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
        0.2,
        "Presence",
        "Sets how loud and upfront the snare sits in the mix.",
    ),
    SliderSpec(
        "tune",
        -12,
        12,
        1,
        0,
        "Pitch",
        "Retunes the drum body in semitones; lower is fatter and heavier, higher is tighter and more ringing.",
    ),
    SliderSpec(
        "snap",
        0.0,
        2.0,
        0.05,
        1.0,
        "Snap",
        "Amount of noisy wire rattle against the drum body; more is wider and crisper, less leaves a "
        "rounder, more tonal hit.",
    ),
    SliderSpec(
        "tone",
        800,
        6000,
        50,
        2000,
        "Brightness",
        "Moves the rattle from fuller and thicker (lower) to thinner and more sizzling (higher).",
    ),
    SliderSpec(
        "decay",
        0.05,
        0.5,
        0.01,
        0.16,
        "Tail",
        "Length of the rattle after the hit; short is a dry crack, long reads like a small room around the snare.",
    ),
    SliderSpec(
        "rate",
        Clock.rate_limits(BASE_DIVISION)[0],
        Clock.rate_limits(BASE_DIVISION)[1],
        1,
        0,
        "Rate",
        "Halves or doubles the snare pattern speed for each step away from its 16th-note grid.",
    ),
)
# step in the 16-step bar -> accent; the quiet final hit is a ghost note
PATTERN = {4: 1.0, 12: 1.0, 15: 0.3}
BODY_FREQ = notes.Fs3
# pitch bend at the strike, as a fraction above the body - kept well below a
# kick's so the snare never turns into a zap or tom
BEND_DEPTH = 0.35
BEND_TIME = 0.02
BODY_DECAY = 0.09
# the rattle is the louder layer; the body gives it a centre
BODY_LEVEL = 0.6
RATTLE_RESONANCE = 1.2
DECAY_CURVE = 3
BEND_CURVE = 6
VOLUME_DEFAULT = 0.3


def _ratio(semitones: float) -> float:
    return 2 ** (semitones / 12)


def build(
    tempo: Tempo,
    clock: Clock,
    level: float = 0.2,
    tune: float = 0,
    snap: float = 1.0,
    tone: float = 2000,
    decay: float = 0.16,
    rate: float = 0,
) -> Patch:
    """Build a tone-plus-rattle snare on the backbeat with a ghost note."""
    trigger = Trig()
    tuning = Sig(_ratio(tune))
    body_freq = tuning * BODY_FREQ

    bend_table = ExpTable([(0, 1), (8191, 0)], exp=BEND_CURVE)
    bend = TrigEnv(trigger, bend_table, dur=BEND_TIME, mul=BEND_DEPTH, add=1)
    pitch = body_freq * bend
    body = Sine(freq=pitch)
    body_table = ExpTable([(0, 1), (8191, 0)], exp=DECAY_CURVE)
    body_env = TrigEnv(trigger, body_table, dur=BODY_DECAY, mul=level * BODY_LEVEL)
    body_signal = body * body_env

    noise = Noise()
    rattle_table = ExpTable([(0, 1), (8191, 0)], exp=DECAY_CURVE)
    rattle_env = TrigEnv(trigger, rattle_table, dur=decay, mul=level * snap)
    rattle_burst = noise * rattle_env
    rattle = Biquad(rattle_burst, freq=tone, q=RATTLE_RESONANCE, type=1)

    voice = body_signal + rattle
    state = {"step": 0, "level": level, "snap": snap, "accent": 1.0}

    def apply_gains() -> None:
        gain = state["level"] * state["accent"]
        body_env.mul = gain * BODY_LEVEL
        rattle_env.mul = gain * state["snap"]

    def next_step() -> None:
        accent = PATTERN.get(state["step"] % 16)
        if accent is not None:
            state["accent"] = accent
            apply_gains()
            # restart the body on a zero crossing so the immediate attack
            # doesn't click wherever the oscillator last stopped
            body.reset()
            trigger.play()
        state["step"] += 1

    def set_gain(name: str, value: float) -> None:
        state[name] = value
        apply_gains()

    division = clock.subscribe(clock.ticks_for_rate(BASE_DIVISION, rate), next_step)
    return Patch(
        sequencer=division,
        voice=voice,
        controls={
            "level": lambda value: set_gain("level", value),
            "tune": lambda value: setattr(tuning, "value", _ratio(value)),
            "snap": lambda value: set_gain("snap", value),
            "tone": lambda value: setattr(rattle, "freq", value),
            "decay": lambda value: setattr(rattle_env, "dur", value),
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
            body_table,
            body_env,
            body_signal,
            noise,
            rattle_table,
            rattle_env,
            rattle_burst,
            rattle,
        ),
    )
