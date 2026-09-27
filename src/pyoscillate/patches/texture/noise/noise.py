# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.texture.noise.noise
"""Filtered-noise bed with a single colour control and four kinds of motion.

One broadband source is shaped four ways, and each style adds a different
kind of movement on top. The source is a `Selector` crossfade over white,
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
- `dust` (`NoiseDust`): a pink/brown-leaning bed layered with sparse,
  randomly-timed click/pop transients (`RandDur` + `Change` - pyo's
  un-clocked randomized-event idiom), so it reads as discrete vinyl dust and
  stylus crackle rather than continuous, steady movement.

All four share one colour-crossfaded source (`Noise.build`); only the
movement stage in `moved_signal()` differs, since that is genuinely
different behavior, not just different profile data (`patches/AGENTS.md`'s
design rule 1). Each style's `moved_signal()` is a hook method: it assigns
its own graph nodes onto `self` and leaves the final moving bed in
`self.moved`, for `Noise.build()` to level and finish.
"""

from __future__ import annotations

from pyo import PyoObject
from pyo.lib._core import Mix
from pyo.lib.filters import Biquad, Phaser
from pyo.lib.generators import BrownNoise, PinkNoise, Sine
from pyo.lib.generators import Noise as WhiteNoise
from pyo.lib.pan import Selector
from pyo.lib.randoms import RandDur
from pyo.lib.tables import ExpTable
from pyo.lib.triggers import Change, TrigEnv

from pyoscillate.patches.base import Patch
from pyoscillate.patches.common import ContinuousVoice, frequency_shift
from pyoscillate.patches.params import Param

STYLES = ("air", "surf", "barber", "dust")

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
# `dust`: sharp-attack, quick-decay click table and its read duration (s)
CLICK_POINTS = [(0, 1.0), (8191, 0.0)]
CLICK_CURVE = 5.0
CLICK_DECAY = 0.01
# per-channel RandDur interval bounds (s) between clicks at Motion 1 -
# unrelated so left/right pops never line up - scaled by 1/Motion so higher
# Motion means more frequent crackle. Pyo's arithmetic operators only expand
# a `list` operand into multiple streams, not a `tuple` (multiplying a
# PyoObject by a tuple crashes natively - see keys/AGENTS.md-style caution in
# patches/AGENTS.md on graph ownership), so these stay lists.
DUST_MIN = [0.05, 0.6]
DUST_MAX = [0.35, 3.0]
DUST_GAIN = 1.3
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

    volume_default = VOLUME_DEFAULT

    colour = Param(
        0,
        2,
        0.05,
        1,
        "Colour",
        "Moves the noise from bright white hiss (0) through softer pink (1) to dark, rumbling brown (2).",
    )
    brightness = Param(
        300,
        12000,
        50,
        5000,
        "Brightness",
        "How much high-end hiss is let through; lower is muffled and distant, higher is airy and close.",
    )
    motion = Param(
        0.25,
        4,
        0.05,
        1,
        "Motion",
        "How fast the bed moves; low is a slow tide, high is a restless flutter.",
    )
    depth = Param(
        0,
        1,
        0.05,
        0.6,
        "Depth",
        "How far the movement swings; zero is a still, steady bed, full is a wide swell or swirl.",
    )
    level = Param(
        0,
        0.5,
        0.01,
        0.35,
        "Level",
        "How loud the noise bed sits under everything else.",
    )

    white: WhiteNoise
    pink: PinkNoise
    brown: BrownNoise
    source: Selector
    moved: PyoObject
    leveled: PyoObject

    def moved_signal(self, live: dict[str, PyoObject], source: PyoObject) -> None:
        """This style's filtered, moving noise bed built from the shared
        colour-crossfaded `source`: assigns every node it builds onto
        `self`, ending with the final bed in `self.moved`. Overridden per
        style."""
        raise NotImplementedError

    def build(self) -> Patch:
        self._reset()
        live = self.live_all("colour", "brightness", "motion", "depth", "level")

        self.white = WhiteNoise(mul=COLOUR_GAINS[0])
        self.pink = PinkNoise(mul=COLOUR_GAINS[1])
        self.brown = BrownNoise(mul=COLOUR_GAINS[2])
        self.source = Selector([self.white, self.pink, self.brown], voice=live["colour"])

        self.moved_signal(live, self.source)
        self.leveled = self.moved * live["level"]
        return self.finish(self.leveled)


class NoiseAir(Noise):
    """Cutoff breathes on two slow, unrelated LFOs, one per channel, so the
    bed opens and closes without ever repeating in step."""

    title = "Noise - Air"

    rates: PyoObject
    swing: PyoObject
    cutoff_lfo: Sine
    cutoff: PyoObject

    def moved_signal(self, live, source):
        self.rates = live["motion"] * AIR_RATES
        self.swing = live["depth"] * AIR_SWING
        self.cutoff_lfo = Sine(freq=self.rates, mul=self.swing, add=1)
        self.cutoff = live["brightness"] * self.cutoff_lfo
        self.moved = Biquad(source, freq=self.cutoff, q=FILTER_Q, type=0)


class NoiseSurf(Noise):
    """A 20-stage `Phaser` whose notch position, spacing and sharpness each
    ride their own slow LFO per channel, summed with the dry bed so the
    notches actually form."""

    title = "Noise - Surf"

    shaped: Biquad
    freq_rates: PyoObject
    freq_swing: PyoObject
    freq_lfo: Sine
    spread_rates: PyoObject
    spread_swing: PyoObject
    spread_lfo: Sine
    q_rates: PyoObject
    q_swing: PyoObject
    q_lfo: Sine
    phased: Phaser
    dry: PyoObject
    notched: PyoObject

    def moved_signal(self, live, source):
        self.shaped = Biquad(source, freq=live["brightness"], q=FILTER_Q, type=0)

        self.freq_rates = live["motion"] * SURF_FREQ[0]
        self.freq_swing = live["depth"] * SURF_FREQ[1]
        self.freq_lfo = Sine(freq=self.freq_rates, mul=self.freq_swing, add=SURF_FREQ[2])

        self.spread_rates = live["motion"] * SURF_SPREAD[0]
        self.spread_swing = live["depth"] * SURF_SPREAD[1]
        self.spread_lfo = Sine(freq=self.spread_rates, mul=self.spread_swing, add=SURF_SPREAD[2])

        self.q_rates = live["motion"] * SURF_Q[0]
        self.q_swing = live["depth"] * SURF_Q[1]
        self.q_lfo = Sine(freq=self.q_rates, mul=self.q_swing, add=SURF_Q[2])

        # pyo's Phaser is a pure allpass cascade: its own output has a flat
        # spectrum, and the notches only appear where it cancels against the
        # dry bed, so the two are summed here
        self.phased = Phaser(
            self.shaped, freq=self.freq_lfo, spread=self.spread_lfo, q=self.q_lfo, num=SURF_NOTCHES
        )
        self.dry = self.shaped.mix(2)
        self.notched = self.dry + self.phased
        self.moved = self.notched * SURF_GAIN


class NoiseBarber(Noise):
    """Single-sideband frequency shift of the bed, mixed with the dry
    sound. A few Hz of shift makes a slow, endless phasing swirl."""

    title = "Noise - Barber"

    shaped: Biquad
    shift_rate_a: PyoObject
    shift_swing_a: PyoObject
    shift_a: Sine
    shifted_a: PyoObject
    shift_rate_b: PyoObject
    shift_swing_b: PyoObject
    shift_b: Sine
    shifted_b: PyoObject
    wet: Mix
    dry: PyoObject

    def moved_signal(self, live, source):
        self.shaped = Biquad(source, freq=live["brightness"], q=FILTER_Q, type=0)

        self.shift_rate_a = live["motion"] * BARBER_RATES[0]
        self.shift_swing_a = live["depth"] * BARBER_SHIFT
        self.shift_a = Sine(freq=self.shift_rate_a, mul=self.shift_swing_a)
        stage_a = frequency_shift(self.shaped, self.shift_a)
        self.shifted_a = stage_a.output
        self.retain(*stage_a.resources)

        self.shift_rate_b = live["motion"] * BARBER_RATES[1]
        self.shift_swing_b = live["depth"] * BARBER_SHIFT
        self.shift_b = Sine(freq=self.shift_rate_b, mul=self.shift_swing_b)
        stage_b = frequency_shift(self.shaped, self.shift_b)
        self.shifted_b = stage_b.output
        self.retain(*stage_b.resources)

        self.wet = Mix([self.shifted_a, self.shifted_b], voices=2, mul=BARBER_WET)
        self.dry = self.shaped.mix(2)
        self.moved = self.dry + self.wet


class NoiseDust(Noise):
    """Pink/brown-leaning noise bed dusted with sparse, randomly-timed
    click/pop transients (`RandDur` + `Change`, pyo's un-clocked randomized-
    event idiom), so the texture reads as vinyl dust and stylus crackle -
    discrete grain - instead of steady hiss or a continuously sweeping bed."""

    title = "Noise - Dust"
    colour = Noise.colour.replace(default=1.4)
    brightness = Noise.brightness.replace(default=3200)
    motion = Noise.motion.replace(
        help_text="How often the crackle pops; low is occasional, sparse clicks, high is a denser flurry."
    )
    depth = Noise.depth.replace(
        help_text="How loud the crackle sits over the bed; zero is a clean noise bed, full is dense clicks "
        "and pops."
    )

    shaped: Biquad
    dry: PyoObject
    motion_scale: PyoObject
    click_min: PyoObject
    click_max: PyoObject
    click_interval: RandDur
    click_trigger: Change
    click_table: ExpTable
    click_noise: WhiteNoise
    click_env: TrigEnv
    click_burst: PyoObject

    def moved_signal(self, live, source):
        self.shaped = Biquad(source, freq=live["brightness"], q=FILTER_Q, type=0)
        self.dry = self.shaped.mix(2)

        # RandDur's own `min`/`max` are the crackle's interval bounds in
        # seconds; dividing by Motion (not multiplying, unlike the other
        # styles' LFO rates) shortens that interval - and so densifies the
        # crackle - as Motion rises
        self.motion_scale = 1 / live["motion"]
        self.click_min = self.motion_scale * DUST_MIN
        self.click_max = self.motion_scale * DUST_MAX
        self.click_interval = RandDur(min=self.click_min, max=self.click_max)
        # a trigger each time RandDur re-picks a new interval - an
        # unpredictable, per-channel pop time
        self.click_trigger = Change(self.click_interval)
        self.click_table = ExpTable(CLICK_POINTS, exp=CLICK_CURVE)
        self.click_noise = WhiteNoise()
        self.click_env = TrigEnv(
            self.click_trigger, self.click_table, dur=CLICK_DECAY, mul=live["depth"] * DUST_GAIN
        )
        self.click_burst = self.click_noise * self.click_env
        self.moved = self.dry + self.click_burst
