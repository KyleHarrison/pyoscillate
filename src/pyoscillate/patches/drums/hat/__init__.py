# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.drums.hat
from __future__ import annotations

from pyo.lib.filters import ButHP
from pyo.lib.generators import Noise, Sine
from pyo.lib.triggers import TrigEnv

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.patches.base import Patch
from pyoscillate.patches.drums.base import DrumVoice
from pyoscillate.patches.params import PyoParamRef, SliderSpec
from pyoscillate.tempo import Tempo

CUTOFF_FREQ = 10300
DECAY = 0.15
BASE_DIVISION = NoteDivision.EIGHTH
# exponent of the decay curve - a sharp, strongly exponential drop keeps the
# hat ticking rather than hissing
DECAY_CURVE = 5
# not defined by this module before conversion to a class - VOLUME_DEFAULT
# lives here now since a class attribute can't take a per-rack override the
# way FunctionVoice.from_module(..., volume_default=) could
VOLUME_DEFAULT = 0.2

PARAMETERS = (
    SliderSpec(
        "cutoff_freq",
        2000,
        12000,
        100,
        CUTOFF_FREQ,
        "Brightness",
        "Moves the tick from fuller and more present (lower) to thinner, airier, and more distant-sounding (higher).",
        (PyoParamRef(ButHP, "freq"),),
    ),
    SliderSpec(
        "level",
        0,
        1,
        0.05,
        0.2,
        "Presence",
        "Sets how upfront the tick sits in the mix, from a subtle texture to a louder, more foregrounded pulse.",
        (PyoParamRef(TrigEnv, "mul"),),
    ),
    SliderSpec(
        "decay",
        0.03,
        0.6,
        0.01,
        DECAY,
        "Tightness",
        "Shapes the tick's tail; shorter feels tight and click-like, longer blurs into more of a hiss.",
        (PyoParamRef(TrigEnv, "dur"),),
    ),
    SliderSpec(
        "rate",
        Clock.rate_limits(BASE_DIVISION)[0],
        Clock.rate_limits(BASE_DIVISION)[1],
        1,
        0,
        "Rate",
        "Halves or doubles the tick pattern speed for each step away from its 8th-note grid.",
    ),
)


class Tick(DrumVoice):
    """Subtle high-passed noise tick, once per 8th note, for top-end texture."""

    name = "hat"
    title = "Hi-hat"
    summary = "Subtle, airy top-end pulse."
    parameters = PARAMETERS
    volume_default = VOLUME_DEFAULT

    def build(
        self,
        tempo: Tempo,
        clock: Clock,
        cutoff_freq: float = CUTOFF_FREQ,
        level: float = 0.2,
        decay: float = DECAY,
        rate: float = 0,
    ) -> Patch:
        """
        Args:
            tempo: Shared tempo grid; the level swell is derived from
                `tempo.sixteenth`.
            clock: Shared master pulse; the hat ticks every 8th note
                (`clock.eighth`), phase-locked to every other patch on the clock.
            cutoff_freq: ButHP high-pass cutoff (Hz). Raising it strips away more
                low and mid content, making the tick thinner, more distant, and
                more "sizzly"; lowering it lets more body through, making the
                tick fatter and more present but less airy.
            level: Peak amplitude of each noise burst, before the swell and
                high-pass are applied. Raising it makes the whole hat louder and
                more upfront in the mix; lowering it pushes it further back as a
                subtle texture.
            decay: Length (seconds) of the tick's exponential amplitude decay.
                Shorter values give a tighter, click-like tick; longer values let
                it decay into more of a hiss, blurring the individual 8th notes
                together.
        """
        self._reset()
        hat_noise = Noise()
        hat_env = self.envelope([(0, 1), (8191, 0)], dur=decay, mul=level, exp=DECAY_CURVE)
        hat_burst = hat_noise * hat_env

        # slow swell over 32 steps so the ticks don't sit at a fixed level
        hat_swell = Sine(freq=1 / (32 * tempo.sixteenth), mul=0.3, add=0.8)

        # high-pass to keep it thin and airy, out of the kick and bass range
        voice = ButHP(hat_burst, freq=cutoff_freq, mul=hat_swell)
        self.retain(hat_noise, hat_burst, hat_swell)

        self.schedule(BASE_DIVISION, rate, clock, self.trigger.play)
        return self.finish(
            voice,
            {
                "cutoff_freq": lambda value: setattr(voice, "freq", value),
                "level": lambda value: setattr(hat_env, "mul", value),
                "decay": lambda value: setattr(hat_env, "dur", value),
            },
        )
