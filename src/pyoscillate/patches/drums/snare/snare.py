# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.drums.snare.snare
"""Tone-and-rattle snare voice.

Two layers share one trigger: a short sine body a little above the kick's
register, with a modest downward pitch bend, and a louder high-passed noise
rattle whose exponential tail runs from a dry crack to a small-room wash. It
sits on the backbeat under the clap, with a ghost note that swings into the
next bar.
"""

from typing import Any

from pyo.lib._core import Sig
from pyo.lib.filters import Biquad
from pyo.lib.generators import Noise, Sine

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.patches.base import Patch
from pyoscillate.patches.drums.base import DrumVoice, semitone_ratio
from pyoscillate.patches.params import SliderSpec, rate_slider
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
    rate_slider(
        BASE_DIVISION,
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


class Snare(DrumVoice):
    """Tone-plus-rattle snare on the backbeat with a ghost note."""

    summary = "Tone-and-rattle backbeat snare with a swung ghost note, layered under the clap."
    parameters = PARAMETERS
    volume_default = VOLUME_DEFAULT

    level: float
    tune: float
    snap: float
    tone: float
    decay: float
    rate: float

    def build(self, tempo: Tempo, clock: Clock, **values: Any) -> Patch:
        self.configure(**values)
        self._reset()
        tuning = Sig(semitone_ratio(self.tune))
        body_freq = tuning * BODY_FREQ

        bend = self.envelope([(0, 1), (8191, 0)], dur=BEND_TIME, mul=BEND_DEPTH, add=1, exp=BEND_CURVE)
        pitch = body_freq * bend
        body = Sine(freq=pitch)
        body_env = self.envelope(
            [(0, 1), (8191, 0)], dur=BODY_DECAY, mul=self.level * BODY_LEVEL, exp=DECAY_CURVE
        )
        body_signal = body * body_env

        noise = Noise()
        rattle_env = self.envelope(
            [(0, 1), (8191, 0)], dur=self.decay, mul=self.level * self.snap, exp=DECAY_CURVE
        )
        rattle_burst = noise * rattle_env
        rattle = Biquad(rattle_burst, freq=self.tone, q=RATTLE_RESONANCE, type=1)

        voice = body_signal + rattle
        self.retain(tuning, body_freq, pitch, body, body_signal, noise, rattle_burst, rattle)
        state = {"level": self.level, "snap": self.snap, "accent": 1.0}

        def apply_gains() -> None:
            gain = state["level"] * state["accent"]
            body_env.mul = gain * BODY_LEVEL
            rattle_env.mul = gain * state["snap"]

        step = self.step_pattern(16, PATTERN)

        def next_step() -> None:
            _, accent = step()
            if accent is not None:
                state["accent"] = accent
                apply_gains()
                # restart the body on a zero crossing so the immediate
                # attack doesn't click wherever the oscillator last stopped
                body.reset()
                self.trigger.play()

        def set_gain(name: str, value: float) -> None:
            state[name] = value
            apply_gains()

        self.schedule(BASE_DIVISION, self.rate, clock, next_step)
        return self.finish(
            voice,
            {
                "level": lambda value: set_gain("level", value),
                "tune": lambda value: setattr(tuning, "value", semitone_ratio(value)),
                "snap": lambda value: set_gain("snap", value),
                "tone": lambda value: setattr(rattle, "freq", value),
                "decay": lambda value: setattr(rattle_env, "dur", value),
            },
        )
