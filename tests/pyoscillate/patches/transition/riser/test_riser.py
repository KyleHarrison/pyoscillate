"""Perceptual contract for the riser: it is silent until its start bar, climbs
in level and brightness, and cuts on the phrase downbeat; Length, Climb,
Surge, Brightness and Level each move their measurable correlate the way the
label promises.

Assertions are directions and tolerance bands, never golden values - see
tests/AGENTS.md. Renders run at 240 BPM so a bar is one second and an
8-bar phrase fits in a short render.
"""

import unittest
from functools import cache

import numpy as np

from pyoscillate.analysis.features import Window, features, spectral_centroid, to_db
from pyoscillate.analysis.render import Render, render
from pyoscillate.patches.base import PATCH_OUTPUT_CEILING
from pyoscillate.patches.transition.riser import riser

MODULE = "pyoscillate.patches.transition.riser.riser"
BPM = 240
BAR = 60 / BPM * 4
DOWNBEAT = riser.PHRASE_BARS * BAR
# render a little past the downbeat so the cut and the silence after it show
SECONDS = DOWNBEAT + 0.3
# the clock fires one audio buffer after the tick (~6 ms); the clap test
# uses the same band
ONSET_TOLERANCE = 0.02
# -80 dBFS: comfortably above numerical noise, far below anything audible
SILENT_PEAK = 1e-4


@cache
def _render(**params: float | str) -> Render:
    return render(MODULE, params, seconds=SECONDS, bpm=BPM)


def _span(result: Render, start: float, end: float) -> np.ndarray:
    rate = result.sample_rate
    return result.samples[round(start * rate) : round(end * rate)]


def _audible(result: Render) -> tuple[float, float]:
    """First and last times the render rises above SILENT_PEAK."""
    loud = np.flatnonzero(np.abs(result.samples) > SILENT_PEAK)
    return loud[0] / result.sample_rate, loud[-1] / result.sample_rate


def _stretch(
    result: Render, fraction: float, length: float, width: float = 0.1
) -> Window:
    """Level and brightness `width` of the riser long, `fraction` of the way in."""
    start = DOWNBEAT - length * BAR * (1 - fraction)
    samples = _span(result, start, start + length * BAR * width)
    return Window(
        start=start,
        rms_db=to_db(float(np.sqrt(np.mean(samples**2)))),
        centroid=spectral_centroid(samples, result.sample_rate),
    )


def _peak(**params: float | str) -> Window:
    """The stretch just before the cut, where the riser is at full height."""
    length = params.get("length", riser.Riser.length.spec.default)
    return _stretch(_render(**params), 0.85, length)


class RiserHealthTests(unittest.TestCase):
    def test_silent_until_its_start_bar_then_cut_on_the_downbeat(self) -> None:
        for style in riser.STYLES:
            for length in (1, 3):
                with self.subTest(style=style, length=length):
                    first, last = _audible(_render(style=style, length=length))

                    # surge 2 starts from zero, so the first audible sample
                    # can trail the start bar slightly, but never lead it
                    start = DOWNBEAT - length * BAR
                    self.assertGreater(first, start - ONSET_TOLERANCE)
                    self.assertLess(first, start + 0.1 * length * BAR)
                    self.assertLess(abs(last - DOWNBEAT), ONSET_TOLERANCE)

    def test_loudest_corner_is_clean_at_default_volume(self) -> None:
        for style in riser.STYLES:
            for climb in (
                riser.Riser.climb.spec.minimum,
                riser.Riser.climb.spec.maximum,
            ):
                with self.subTest(style=style, climb=climb):
                    loudest = features(
                        _render(
                            style=style,
                            length=1,
                            climb=climb,
                            surge=riser.Riser.surge.spec.minimum,
                            brightness=riser.Riser.brightness.spec.maximum,
                            level=riser.Riser.level.spec.maximum,
                        ),
                        ceiling=PATCH_OUTPUT_CEILING,
                    )

                    self.assertEqual(loudest.clip_fraction, 0.0)


class RiserControlTests(unittest.TestCase):
    def test_every_style_climbs_in_level_and_brightness(self) -> None:
        for style in riser.STYLES:
            with self.subTest(style=style):
                result = _render(style=style, length=2)
                early = _stretch(result, 0.25, 2)
                late = _stretch(result, 0.85, 2)

                self.assertGreater(late.rms_db - early.rms_db, 12)
                self.assertGreater(late.centroid, early.centroid * 1.3)

    def test_climb_raises_the_peak(self) -> None:
        # `shift` is left out: its partials move by Hz, so the centroid rise
        # is small against the brightness filter and measured in the test above
        for style in ("noise", "pitch"):
            with self.subTest(style=style):
                short = _peak(style=style, climb=0.5)
                far = _peak(style=style, climb=4)

                self.assertGreater(far.centroid, short.centroid * 1.5)

    def test_surge_holds_the_energy_back(self) -> None:
        for style in riser.STYLES:
            with self.subTest(style=style):
                early_rise = _render(
                    style=style, length=4, surge=riser.Riser.surge.spec.minimum
                )
                late_surge = _render(
                    style=style, length=4, surge=riser.Riser.surge.spec.maximum
                )

                def midpoint_gap(result: Render) -> float:
                    return (
                        _stretch(result, 0.85, 4).rms_db
                        - _stretch(result, 0.5, 4).rms_db
                    )

                self.assertGreater(
                    midpoint_gap(late_surge) - midpoint_gap(early_rise), 6
                )

    def test_brightness_opens_the_peak(self) -> None:
        dull = _peak(style="noise", brightness=2000)
        bright = _peak(style="noise", brightness=16000)

        self.assertGreater(bright.centroid, dull.centroid * 1.5)

    def test_level_raises_the_peak_loudness(self) -> None:
        quiet = _peak(style="pitch", level=0.1)
        loud = _peak(style="pitch", level=0.2)

        self.assertGreater(loud.rms_db - quiet.rms_db, 4.0)
        self.assertLess(loud.rms_db - quiet.rms_db, 8.0)


if __name__ == "__main__":
    unittest.main()
