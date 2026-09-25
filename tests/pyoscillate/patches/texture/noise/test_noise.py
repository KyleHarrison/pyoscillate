"""Perceptual contract for the noise bed: colour, brightness, level and
movement each move their measurable correlate the way the label promises.

Assertions are directions and tolerance bands, never golden values - see
tests/CLAUDE.md.

Findings
========

1. The `surf` profile did not move
----------------------------------
Error:
    With Depth 0 and Depth 1 (Motion 4), `surf` measured the same spectral
    movement, 1.05 dB, which is the estimation noise floor of a still bed.
    `air` rose from 1.04 to 3.68 dB and `barber` from 1.04 to 2.63 dB.
Cause:
    pyo's `Phaser` is a pure allpass cascade. Its output alone has a flat
    magnitude spectrum: an offline check with fixed settings showed no
    notch anywhere between 200 Hz and 1.9 kHz. The notches only form where
    the phase-shifted copy cancels against the dry signal. The pyo example
    this profile was ported from (x06/04) sends only the `Phaser` output, so
    it only moves the stereo phase, not the spectrum.
Change:
    Sum the dry bed with the `Phaser` output and halve the result
    (`SURF_GAIN` 0.5) so the level stays in line with the other profiles.
    Measured after the change: 1.19 dB still, 1.9 dB moving.
Status:
    fixed in texture/noise/noise.py.
"""

import unittest
from functools import cache

import numpy as np

from pyoscillate.analysis.features import (
    Features,
    Window,
    features,
    spectral_movement,
    windows,
)
from pyoscillate.analysis.render import render
from pyoscillate.patches.base import PATCH_OUTPUT_CEILING
from pyoscillate.patches.texture.noise import noise

MODULE = "pyoscillate.patches.texture.noise.noise"
SECONDS = 4.0
SLIDERS = {spec.name: spec for spec in noise.PARAMETERS}


@cache
def _render(**params: float | str):
    return render(MODULE, params, seconds=SECONDS)


def _measure(**params: float | str) -> Features:
    return features(_render(**params), ceiling=PATCH_OUTPUT_CEILING)


def _windows(**params: float | str) -> tuple[Window, ...]:
    # skip the first window: it holds the BuiltPatch.start() fade-in
    return windows(_render(**params))[1:]


def _centroid(**params: float | str) -> float:
    return float(np.median([window.centroid for window in _windows(**params)]))


def _movement(**params: float | str) -> float:
    return spectral_movement(_windows(**params))


class NoiseHealthTests(unittest.TestCase):
    def test_loudest_corner_is_clean_at_default_volume(self) -> None:
        for style in noise.STYLES:
            with self.subTest(style=style):
                loudest = _measure(
                    style=style,
                    colour=SLIDERS["colour"].minimum,
                    brightness=SLIDERS["brightness"].maximum,
                    depth=SLIDERS["depth"].maximum,
                    level=SLIDERS["level"].maximum,
                )

                self.assertEqual(loudest.clip_fraction, 0.0)

    def test_every_style_sounds_at_its_defaults(self) -> None:
        for style in noise.STYLES:
            with self.subTest(style=style):
                self.assertGreater(_measure(style=style).rms_db, -60)


class NoiseControlTests(unittest.TestCase):
    def test_colour_darkens_the_bed(self) -> None:
        white = _centroid(colour=0, brightness=SLIDERS["brightness"].maximum)
        brown = _centroid(colour=2, brightness=SLIDERS["brightness"].maximum)

        self.assertGreater(white, brown * 4)

    def test_brightness_raises_the_spectral_centroid(self) -> None:
        dull = _centroid(colour=0, brightness=1000)
        bright = _centroid(colour=0, brightness=8000)

        self.assertGreater(bright, dull * 1.5)

    def test_level_raises_the_loudness(self) -> None:
        quiet = _measure(level=0.1)
        loud = _measure(level=0.2)

        self.assertGreater(loud.rms_db - quiet.rms_db, 4.0)
        self.assertLess(loud.rms_db - quiet.rms_db, 8.0)

    def test_depth_adds_movement(self) -> None:
        for style in noise.STYLES:
            with self.subTest(style=style):
                still = _movement(style=style, colour=0, motion=4, depth=0)
                moving = _movement(style=style, colour=0, motion=4, depth=1)

                # the still bed's figure is the estimation noise floor (~1 dB)
                self.assertGreater(moving - still, 0.5)


if __name__ == "__main__":
    unittest.main()
