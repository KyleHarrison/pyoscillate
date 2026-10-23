"""Perceptual contract for the subtractive synth leads (`lead/synth.py`): every
style sounds only once the shared clock ticks, stays under the patch ceiling
even at the loudest sliders, and Brightness opens the filter.

Assertions are directions and tolerance bands, never golden values - see
tests/AGENTS.md.
"""

import unittest
from functools import cache

import numpy as np

from pyoscillate.analysis.features import features
from pyoscillate.analysis.render import Render, render
from pyoscillate.analysis.spectrum import Spectrum
from pyoscillate.patches.base import PATCH_OUTPUT_CEILING
from pyoscillate.patches.tonal.lead.synth import (
    MonoSolo,
    NewAgeLead,
    RnbSlide,
    ScreamingSync,
    StringsPwm,
    SynthLead,
    Trance5th,
)

RATE = 44100
BPM = 120
MODULE = "pyoscillate.patches.tonal.lead.synth"
STYLES = {
    "solo": MonoSolo,
    "lead": NewAgeLead,
    "slide": RnbSlide,
    "sync": ScreamingSync,
    "pwm": StringsPwm,
    "trance5th": Trance5th,
}
LOUDEST = {
    "brightness": SynthLead.brightness.spec.maximum,
    "drive": SynthLead.drive.spec.maximum,
    "detune": SynthLead.detune.spec.maximum,
}


@cache
def _render(style: str, seconds: float = 6.0, **params: float) -> Render:
    return render(MODULE, {"style": style, **params}, seconds=seconds, bpm=BPM)


class HealthTests(unittest.TestCase):
    def test_every_style_is_silent_until_the_shared_clock_ticks(self) -> None:
        for style in STYLES:
            with self.subTest(style=style):
                result = features(
                    render(MODULE, {"style": style}, seconds=0.5, clock_running=False)
                )

                self.assertLess(result.peak, 1e-4)

    def test_every_style_sounds_after_the_clock_starts(self) -> None:
        for style in STYLES:
            with self.subTest(style=style):
                self.assertGreater(features(_render(style)).peak, 1e-3)

    def test_output_stays_under_the_patch_ceiling(self) -> None:
        for style in STYLES:
            with self.subTest(style=style):
                self.assertLess(
                    float(abs(_render(style).samples).max()), PATCH_OUTPUT_CEILING
                )

    def test_the_loudest_corner_neither_clips_nor_runs_away(self) -> None:
        for style in STYLES:
            with self.subTest(style=style):
                samples = _render(style, **LOUDEST).samples

                self.assertLess(float(abs(samples).max()), PATCH_OUTPUT_CEILING)
                # the filter ran away and fell silent
                self.assertGreater(float(abs(samples[-2 * RATE :]).max()), 1e-4)

    def test_each_style_has_its_own_name(self) -> None:
        names = [cls.name for cls in STYLES.values()]

        self.assertEqual(len(set(names)), len(names))


class FilterTests(unittest.TestCase):
    def test_brightness_opens_the_filter(self) -> None:
        def treble(brightness: float) -> float:
            samples = _render("lead", brightness=brightness).samples
            return Spectrum.of(samples[RATE : 5 * RATE], RATE).share(2000, 20000)

        self.assertGreater(treble(6000), 1.5 * treble(0))

    def test_a_wide_open_filter_keeps_the_pulses_edge(self) -> None:
        # Trance 5th's filter rests wide open and has no envelope, so its
        # squares keep upper partials a filter at 1.4 kHz takes away
        def treble(style: str) -> float:
            samples = _render(style, brightness=0).samples
            return Spectrum.of(samples[RATE : 5 * RATE], RATE).share(3000, 20000)

        self.assertGreater(treble("trance5th"), 2 * treble("lead"))

    def test_styles_do_not_sound_alike(self) -> None:
        centroids = {
            style: Spectrum.of(_render(style).samples[RATE : 5 * RATE], RATE).centroid()
            for style in STYLES
        }

        self.assertGreater(float(np.std(list(centroids.values()))), 20)


if __name__ == "__main__":
    unittest.main()
