"""Contract for the wobble bass: the wobble is locked to the tempo, its depth
moves the tone, and it is silent until the clock runs.

The first bar sits under `Patch.start()`'s fade-in, so tone is measured from
the second bar onward.
"""

import unittest
from functools import cache

import numpy as np

from pyoscillate.analysis.render import Render, render
from pyoscillate.clock import Clock
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import BuildContext, start_server
from pyoscillate.patches.tonal.bass.reese.reese import Reese, ReeseHeave, ReeseWobble
from pyoscillate.tempo import Tempo

MODULE = "pyoscillate.patches.tonal.bass.reese.reese"
BPM = 140
WINDOW = 0.05


def _centroids(result: Render, start: float, stop: float) -> list[float]:
    rate = result.sample_rate
    size = round(WINDOW * rate)
    values = []
    for first in range(round(start * rate), round(stop * rate) - size, size):
        segment = result.samples[first : first + size] * np.hanning(size)
        magnitude = np.abs(np.fft.rfft(segment))
        frequency = np.fft.rfftfreq(size, 1 / rate)
        if magnitude.sum() > 1e-6:
            values.append(float((magnitude * frequency).sum() / magnitude.sum()))
    return values


@cache
def _held_note(depth: float) -> Render:
    return render(
        MODULE,
        {"style": "heave", "depth": depth, "speed": 3},
        seconds=3.6,
        bpm=BPM,
    )


class ReeseWobbleTests(unittest.TestCase):
    def test_speed_options_match_the_wobble_fractions(self) -> None:
        self.assertEqual(len(Reese.WOBBLE_BARS), len(Reese.WOBBLE_LABELS))
        self.assertEqual(Reese.speed.spec.maximum, len(Reese.WOBBLE_BARS) - 1)
        self.assertEqual(Reese.speed.spec.options, Reese.WOBBLE_LABELS)

    def test_styles_start_on_their_own_speed(self) -> None:
        self.assertEqual(Reese.WOBBLE_LABELS[int(ReeseWobble().speed)], "1/8")
        self.assertEqual(Reese.WOBBLE_LABELS[int(ReeseHeave().speed)], "1/2")

    def test_wobble_depth_moves_the_tone_across_a_held_note(self) -> None:
        flat = _centroids(_held_note(0.0), 2.0, 3.4)
        wide = _centroids(_held_note(4.0), 2.0, 3.4)

        self.assertGreater(np.std(wide), 3 * np.std(flat))

    def test_silent_until_the_clock_ticks(self) -> None:
        result = render(
            MODULE, {"style": "wobble"}, seconds=1.0, bpm=BPM, clock_running=False
        )

        self.assertLess(float(np.abs(result.samples).max()), 1e-4)


class ReeseRetempoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = start_server(audio="manual")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.stop()
        cls.server.shutdown()

    def test_wobble_period_is_a_fraction_of_the_bar_and_follows_bpm(self) -> None:
        tempo = Tempo(bpm=BPM)
        patch = ReeseWobble().build(BuildContext(tempo, Clock(tempo), Harmony()))

        self.assertAlmostEqual(patch.wobble_lfo.freq, 1 / (tempo.bar / 8))
        tempo.set_bpm(70)
        patch.retempo()
        self.assertAlmostEqual(patch.wobble_lfo.freq, 1 / (tempo.bar / 8))

    def test_speed_changes_the_wobble_rate(self) -> None:
        tempo = Tempo(bpm=BPM)
        patch = ReeseWobble().build(BuildContext(tempo, Clock(tempo), Harmony()))
        before = patch.wobble_lfo.freq

        patch.speed = 5

        self.assertAlmostEqual(patch.wobble_lfo.freq, before * 2)


if __name__ == "__main__":
    unittest.main()
