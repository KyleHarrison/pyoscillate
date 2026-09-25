# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.texture.noise.noise
"""Filtered-noise bed with a single colour control and three kinds of motion.

One broadband source is shaped three ways, and each style adds a different
kind of slow movement on top. The source is a `Selector` crossfade over white,
pink and brown noise (pyo example x03/04), so "colour" is one continuous
control instead of a choice. A low-pass then sets how much hiss survives.

- `air` (`NoiseAir`): the cutoff itself breathes on two slow, unrelated LFOs,
  one per channel, so the bed opens and closes without ever repeating in step.
- `surf` (`NoiseSurf`): a 20-stage `Phaser` whose notch position, spacing and
  sharpness each ride their own slow LFO per channel (x06/04), summed with the
  dry bed so the notches actually form. The notches sweeping through the
  noise read as surf or wind.
- `barber` (`NoiseBarber`): single-sideband frequency shift of the bed, mixed
  with the dry sound (x06/07). A few Hz of shift makes a slow, endless
  phasing swirl against the dry noise; separate shift LFOs per channel make
  it spin across the stereo field.

All three share one colour-crossfaded source (`Noise.build`); only the
movement stage in `moved_signal()` differs, since that is genuinely
different behavior, not just different profile data (`patches/CLAUDE.md`'s
design rule 1).
"""

from __future__ import annotations

from typing import Any

from pyo import PyoObject
from pyo.lib._core import Mix
from pyo.lib.filters import Biquad, Phaser
from pyo.lib.generators import BrownNoise, PinkNoise, Sine
from pyo.lib.generators import Noise as WhiteNoise
from pyo.lib.pan import Selector

from pyoscillate.patches.base import Patch
from pyoscillate.patches.common import ContinuousVoice, frequency_shift
from pyoscillate.patches.params import SliderSpec

STYLES = ("air", "surf", "barber")

PARAMETERS = (
    SliderSpec(
        "colour",
        0,
        2,
        0.05,
        1,
        "Colour",
        "Moves the noise from bright white hiss (0) through softer pink (1) to dark, rumbling brown (2).",
    ),
    SliderSpec(
        "brightness",
        300,
        12000,
        50,
        5000,
        "Brightness",
        "How much high-end hiss is let through; lower is muffled and distant, higher is airy and close.",
    ),
    SliderSpec(
        "motion",
        0.25,
        4,
        0.05,
        1,
        "Motion",
        "How fast the bed moves; low is a slow tide, high is a restless flutter.",
    ),
    SliderSpec(
        "depth",
        0,
        1,
        0.05,
        0.6,
        "Depth",
        "How far the movement swings; zero is a still, steady bed, full is a wide swell or swirl.",
    ),
    SliderSpec(
        "level",
        0,
        0.5,
        0.01,
        0.35,
        "Level",
        "How loud the noise bed sits under everything else.",
    ),
)
# low-pass Q just under Butterworth, so the cutoff never rings or whistles
FILTER_Q = 0.7
# `air`: per-channel cutoff LFO rates (Hz) at Motion 1 - unrelated so the
# channels drift against each other - and the widest swing, as a fraction of
# the cutoff
AIR_RATES = [0.05, 0.07]
AIR_SWING = 0.7
# `surf`: x06/04's per-channel LFOs as (rates at Motion 1, depth, centre) for
# the first notch frequency, the notch spread and the notch Q
SURF_FREQ = ([0.1, 0.15], 100, 250)
SURF_SPREAD = ([0.18, 0.13], 0.4, 1.5)
SURF_Q = ([0.07, 0.09], 5, 6)
SURF_NOTCHES = 20
# dry + allpass doubles the level wherever the two are in phase; halving it
# keeps `surf` level with the other styles
SURF_GAIN = 0.5
# `barber`: x06/07's shift LFO rates (Hz) and widest shift (Hz), one per channel
BARBER_RATES = (0.03, 0.05)
BARBER_SHIFT = 6
# the example's wet level; with the dry bed added, a quieter shifted copy
# keeps the swirl from doubling the loudness
BARBER_WET = 0.7
# brown noise is the loudest colour once low-passed; this keeps the three
# colours in the same loudness range at the default brightness
COLOUR_GAINS = (1.0, 1.0, 0.8)
# the widest Level with the brightest white noise peaks near 1.0 before the
# volume stage, so this keeps every slider position under the output ceiling
VOLUME_DEFAULT = 0.16


class Noise(ContinuousVoice):
    """Filtered-noise bed with a single colour control; style variants
    subclass this and override `moved_signal()` for their own kind of
    movement - cutoff breathing, notch sweep, or frequency shift."""

    parameters = PARAMETERS
    volume_default = VOLUME_DEFAULT

    colour: float
    brightness: float
    motion: float
    depth: float
    level: float

    def moved_signal(
        self, live: dict[str, Any], source: PyoObject
    ) -> tuple[PyoObject, tuple[Any, ...]]:
        """This style's filtered, moving noise bed built from the shared
        colour-crossfaded `source`, plus any extra Pyo objects it built for
        `build()` to retain. Overridden per style."""
        raise NotImplementedError

    def build(self, **values: Any) -> Patch:
        self.configure(**values)
        self._reset()
        live = self.live_all("colour", "brightness", "motion", "depth", "level")

        white = WhiteNoise(mul=COLOUR_GAINS[0])
        pink = PinkNoise(mul=COLOUR_GAINS[1])
        brown = BrownNoise(mul=COLOUR_GAINS[2])
        source = Selector([white, pink, brown], voice=live["colour"])
        self.retain(white, pink, brown, source)

        moved, resources = self.moved_signal(live, source)
        self.retain(*resources)

        voice = moved * live["level"]
        return self.finish(voice)


class NoiseAir(Noise):
    """Cutoff breathes on two slow, unrelated LFOs, one per channel, so the
    bed opens and closes without ever repeating in step."""

    title = "Noise - Air"

    def moved_signal(self, live, source):
        rates = live["motion"] * AIR_RATES
        swing = live["depth"] * AIR_SWING
        cutoff_lfo = Sine(freq=rates, mul=swing, add=1)
        cutoff = live["brightness"] * cutoff_lfo
        shaped = Biquad(source, freq=cutoff, q=FILTER_Q, type=0)
        return shaped, (rates, swing, cutoff_lfo, cutoff, shaped)


class NoiseSurf(Noise):
    """A 20-stage `Phaser` whose notch position, spacing and sharpness each
    ride their own slow LFO per channel, summed with the dry bed so the
    notches actually form."""

    title = "Noise - Surf"

    def moved_signal(self, live, source):
        shaped = Biquad(source, freq=live["brightness"], q=FILTER_Q, type=0)
        resources: list[Any] = [shaped]

        lfos = []
        for rates, swing, centre in (SURF_FREQ, SURF_SPREAD, SURF_Q):
            lfo_rates = live["motion"] * rates
            lfo_swing = live["depth"] * swing
            lfo = Sine(freq=lfo_rates, mul=lfo_swing, add=centre)
            lfos.append(lfo)
            resources += [lfo_rates, lfo_swing, lfo]

        # pyo's Phaser is a pure allpass cascade: its own output has a flat
        # spectrum, and the notches only appear where it cancels against the
        # dry bed, so the two are summed here
        phased = Phaser(shaped, freq=lfos[0], spread=lfos[1], q=lfos[2], num=SURF_NOTCHES)
        dry = shaped.mix(2)
        notched = dry + phased
        moved = notched * SURF_GAIN
        resources += [phased, dry, notched, moved]
        return moved, tuple(resources)


class NoiseBarber(Noise):
    """Single-sideband frequency shift of the bed, mixed with the dry
    sound. A few Hz of shift makes a slow, endless phasing swirl."""

    title = "Noise - Barber"

    def moved_signal(self, live, source):
        shaped = Biquad(source, freq=live["brightness"], q=FILTER_Q, type=0)
        resources: list[Any] = [shaped]

        wet_channels = []
        for rate in BARBER_RATES:
            shift_rate = live["motion"] * rate
            shift_swing = live["depth"] * BARBER_SHIFT
            shift = Sine(freq=shift_rate, mul=shift_swing)
            shifted = frequency_shift(shaped, shift)
            wet_channels.append(shifted.output)
            resources += [shift_rate, shift_swing, shift, *shifted.resources, shifted.output]
        wet = Mix(wet_channels, voices=2, mul=BARBER_WET)
        dry = shaped.mix(2)
        moved = dry + wet
        resources += [wet, dry, moved]
        return moved, tuple(resources)
