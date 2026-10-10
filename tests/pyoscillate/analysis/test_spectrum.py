"""The spectral and modulation measurements, on signals whose answer is known."""

import math
import unittest

import numpy as np

from pyoscillate.analysis.spectrum import Spectrum, Wobble

RATE = 44100


def _sine(freq: float, seconds: float = 0.5, level: float = 1.0) -> np.ndarray:
    return level * np.sin(2 * np.pi * freq * np.arange(round(seconds * RATE)) / RATE)


class SpectrumTests(unittest.TestCase):
    def test_a_sine_peaks_at_its_own_frequency(self) -> None:
        spectrum = Spectrum.of(_sine(440.0), RATE)

        self.assertAlmostEqual(spectrum.peak_frequency(100, 2000), 440.0, delta=0.5)

    def test_the_peak_is_interpolated_between_bins(self) -> None:
        # 440.37 Hz sits between bins of a 0.5 s window (2 Hz apart, padded 8x)
        spectrum = Spectrum.of(_sine(440.37), RATE)

        self.assertAlmostEqual(spectrum.peak_frequency(100, 2000), 440.37, delta=0.2)

    def test_a_band_holds_the_power_inside_it(self) -> None:
        spectrum = Spectrum.of(_sine(440.0) + _sine(3000.0), RATE)

        self.assertAlmostEqual(spectrum.share(300, 600), 0.5, delta=0.02)
        self.assertAlmostEqual(spectrum.share(2500, 3500), 0.5, delta=0.02)
        self.assertAlmostEqual(spectrum.share(0, 20000), 1.0)

    def test_the_centroid_is_the_power_weighted_mean(self) -> None:
        spectrum = Spectrum.of(_sine(1000.0) + _sine(3000.0), RATE)

        self.assertAlmostEqual(spectrum.centroid(), 2000.0, delta=20)

    def test_a_partial_stands_well_above_the_spectrum_around_it(self) -> None:
        spectrum = Spectrum.of(_sine(440.0), RATE)

        self.assertGreater(
            spectrum.peak_near(440.0, 2), 1000 * spectrum.floor_near(440.0, 40)
        )

    def test_partial_levels_follow_the_harmonics(self) -> None:
        samples = _sine(220.0) + 0.5 * _sine(440.0) + 0.25 * _sine(660.0)

        levels = Spectrum.of(samples, RATE).partial_levels(220.0, 3)

        self.assertAlmostEqual(levels[1] - levels[0], 20 * math.log10(0.5), delta=0.5)
        self.assertAlmostEqual(levels[2] - levels[0], 20 * math.log10(0.25), delta=0.5)


class WobbleTests(unittest.TestCase):
    def _tremolo(self, rate: float, depth: float) -> np.ndarray:
        seconds = 2.0
        times = np.arange(round(seconds * RATE)) / RATE
        return (1 - depth * (1 - np.sin(2 * np.pi * rate * times)) / 2) * _sine(
            1000.0, seconds
        )

    def test_a_steady_tone_does_not_swing_in_level(self) -> None:
        self.assertLess(Wobble.level(_sine(1000.0), RATE, 0.02), 0.05)

    def test_a_tremolo_swings_in_level_by_its_depth(self) -> None:
        swing = Wobble.level(self._tremolo(4.0, 0.5), RATE, 0.02)

        self.assertGreater(swing, 0.3)

    def test_the_level_swings_at_the_tremolo_speed(self) -> None:
        samples = self._tremolo(6.0, 0.8)

        self.assertAlmostEqual(Wobble.level_rate(samples, RATE), 6.0, delta=0.5)

    def test_a_vibrato_swings_the_pitch_by_its_depth(self) -> None:
        seconds = 1.0
        times = np.arange(round(seconds * RATE)) / RATE
        cents = 40.0
        phase = 2 * np.pi * 1000.0 * times + (
            1000.0 * (2 ** (cents / 1200) - 1) / 5.0 * np.sin(2 * np.pi * 5.0 * times)
        )

        swing = Wobble.pitch(np.sin(phase), RATE, 500, 2000)

        self.assertGreater(swing, 0.4 * cents)
        self.assertLess(swing, 2.5 * cents)

    def test_a_steady_pitch_does_not_swing(self) -> None:
        self.assertLess(Wobble.pitch(_sine(1000.0), RATE, 500, 2000), 3)


if __name__ == "__main__":
    unittest.main()
