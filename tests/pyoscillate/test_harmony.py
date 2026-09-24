import math
import unittest
from unittest.mock import MagicMock, patch

from pyoscillate.clock import Clock
from pyoscillate.harmony import A, Harmony
from pyoscillate.tempo import Tempo


def semitones_between(low: float, high: float) -> float:
    return 12 * math.log2(high / low)


class HarmonyTests(unittest.TestCase):
    def test_key_snaps_to_the_nearest_octave_of_the_centre(self) -> None:
        self.assertAlmostEqual(Harmony(key=A).key_freq(55), 55)
        self.assertAlmostEqual(Harmony(key=A).key_freq(100), 110)

    def test_every_chord_root_stays_within_a_tritone_of_the_centre(self) -> None:
        harmony = Harmony(key=A, progression=(0, 5, 10, 7))
        for key in range(12):
            harmony.key = key
            for bar in range(4):
                with self.subTest(key=key, bar=bar):
                    root = harmony.chord_freq(146, bar)
                    self.assertLessEqual(abs(semitones_between(146, root)), 6)

    def test_progression_advances_on_bars_and_wraps(self) -> None:
        harmony = Harmony(key=A, progression=(0, 5, 10, 7), bars_per_chord=2)

        self.assertEqual(
            [harmony.chord_offset(bar) for bar in range(10)],
            [0, 0, 5, 5, 10, 10, 7, 7, 0, 0],
        )

    def test_chord_root_is_the_progression_step_above_the_key(self) -> None:
        harmony = Harmony(key=A, progression=(0, 5, 10, 7))

        # A1, then D2 above it, then G1 and E1 below - the nearest octaves
        expected = [55.0, 73.416, 48.999, 41.203]
        for bar, frequency in enumerate(expected):
            self.assertAlmostEqual(harmony.chord_freq(55, bar), frequency, places=2)


class ClockBarIndexTests(unittest.TestCase):
    @patch("pyoscillate.clock.Pattern")
    def test_bar_index_counts_whole_bars_of_ticks(self, _: MagicMock) -> None:
        clock = Clock(Tempo(bpm=120), ticks_per_bar=16)
        indices = []
        for _tick in range(40):
            indices.append(clock.bar_index)
            clock._advance()

        self.assertEqual(indices, [0] * 16 + [1] * 16 + [2] * 8)


if __name__ == "__main__":
    unittest.main()
