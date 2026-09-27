"""The wash should retain a pitch centre and a continuous bed beneath its echoes.

Findings
========

1. Echo spacing mutes the wash until the first repeat
-----------------------------------------------------
Error:
    At 0.8 s echo spacing the first 0.4-0.6 s is silent (RMS 0); at 0.05 s
    spacing it measures 0.0044 RMS. The drone should be audible before an echo.
Cause:
    `Delay` is the only output; its input never reaches the listener directly.
Change:
    The direct reverb voice is mixed with a 0.3-level delayed branch; the
    same early window is now audible and the regression test passes.
Status:
    fixed - src/pyoscillate/patches/tonal/drone/wash.py.

2. The default saw overwhelms the wash with upper harmonics
-----------------------------------------------------------
Error:
    At the default Register (164.814 Hz), the 1-2 s centroid was 961 Hz,
    above five times the fundamental (824 Hz).
Cause:
    Seven saw oscillators feed the chorus and reverb without spectral shaping.
Change:
    A `Tone` low-pass at four times Register softens the source while keeping
    the pitch centre. The register-relative brightness test passes.
Status:
    fixed - src/pyoscillate/patches/tonal/drone/wash.py.

3. Spatial smear was static apart from the chorus's own fast modulation
-----------------------------------------------------------------------
Error:
    The chorus blend control was a constant signal, leaving no slow spatial
    progression unless a slider or rack evolution changed it.
Cause:
    The only free-running modulation drove pitch by at most 1 Hz; it did not
    drive any spatial control.
Change:
    A 0.12 Hz sine moves the chorus blend between 20% and 100% of its
    slider value. Relative to the dry render, the effect difference moves
    from about 0.79 at 2 s to 0.16 at 6 s.
Status:
    fixed - src/pyoscillate/patches/tonal/drone/wash.py.
"""

import unittest
from functools import cache

import numpy as np

from pyoscillate.analysis.features import spectral_centroid
from pyoscillate.analysis.render import Render, render
from pyoscillate.patches.tonal.drone.wash import SoundscapeWash

MODULE = "pyoscillate.patches.tonal.drone.wash"


@cache
def _render(root_freq: float) -> Render:
    return render(MODULE, {"root_freq": root_freq}, seconds=2.0)


@cache
def _motion_render(chorus_bal: float) -> Render:
    return render(MODULE, {"chorus_bal": chorus_bal}, seconds=7.0)


def _energy_near(power: np.ndarray, frequencies: np.ndarray, frequency: float) -> float:
    return float(power[np.abs(frequencies - frequency) < 5].sum())


class WashHealthTests(unittest.TestCase):
    def test_register_retains_a_pitched_centre(self) -> None:
        for root_freq in (
            SoundscapeWash.root_freq.spec.default,
            SoundscapeWash.root_freq.spec.maximum,
        ):
            with self.subTest(root_freq=root_freq):
                result = _render(root_freq)
                samples = result.samples[result.sample_rate :]
                power = np.abs(np.fft.rfft(samples * np.hanning(samples.size))) ** 2
                frequencies = np.fft.rfftfreq(samples.size, 1 / result.sample_rate)

                harmonics = sum(
                    _energy_near(power, frequencies, root_freq * index) for index in range(1, 11)
                )
                between = sum(
                    _energy_near(power, frequencies, root_freq * (index + 0.5))
                    for index in range(1, 11)
                )

                self.assertGreater(harmonics, between * 10)
                self.assertGreater(harmonics, 0)

    def test_echo_spacing_preserves_the_direct_wash(self) -> None:
        early = []
        for delay_time in (
            SoundscapeWash.delay_time.spec.minimum,
            SoundscapeWash.delay_time.spec.default,
        ):
            result = render(MODULE, {"delay_time": delay_time}, seconds=1.0)
            samples = result.samples[
                round(0.4 * result.sample_rate) : round(0.6 * result.sample_rate)
            ]
            early.append(float(np.sqrt(np.mean(samples**2))))

        self.assertGreater(early[1], early[0] * 0.5)

    def test_default_wash_keeps_brightness_near_its_register(self) -> None:
        root_freq = SoundscapeWash.root_freq.spec.default
        result = _render(root_freq)
        samples = result.samples[result.sample_rate : 2 * result.sample_rate]

        self.assertLess(spectral_centroid(samples, result.sample_rate), root_freq * 5)

    def test_chorus_blend_moves_over_a_slow_cycle(self) -> None:
        dry = _motion_render(0)
        wet = _motion_render(SoundscapeWash.chorus_bal.spec.default)

        def effect_fraction(start: float) -> float:
            first = round(start * dry.sample_rate)
            last = first + dry.sample_rate
            reference = dry.samples[first:last]
            difference = wet.samples[first:last] - reference
            return float(np.sqrt(np.mean(difference**2) / np.mean(reference**2)))

        self.assertGreater(effect_fraction(1.5), effect_fraction(5.5) * 2)


if __name__ == "__main__":
    unittest.main()
