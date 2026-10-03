import math
import unittest
from unittest.mock import MagicMock, patch

from pyoscillate.clock import Clock
from pyoscillate.harmony import Harmony
from pyoscillate.tempo import Tempo
from pyoscillate.theory.chord import Chords
from pyoscillate.theory.pitch import Note
from pyoscillate.theory.progression import ChordChanges, Progressions
from pyoscillate.theory.scale import Scales


def semitones_between(low: float, high: float) -> float:
    return 12 * math.log2(high / low)


class HarmonyTests(unittest.TestCase):
    def test_key_snaps_to_the_nearest_octave_of_the_centre(self) -> None:
        self.assertAlmostEqual(Harmony(key=Note.KEY_A).key_freq(55), 55)
        self.assertAlmostEqual(Harmony(key=Note.KEY_A).key_freq(100), 110)

    def test_every_chord_root_stays_within_a_tritone_of_the_centre(self) -> None:
        harmony = Harmony(key=Note.KEY_A)
        for key in range(12):
            harmony.key = key
            for bar in range(4):
                with self.subTest(key=key, bar=bar):
                    root = harmony.chord_freq(146, bar, Progressions.DEEP_HOUSE_MINOR)
                    self.assertLessEqual(abs(semitones_between(146, root)), 6)

    def test_progression_advances_on_bars_and_wraps(self) -> None:
        harmony = Harmony(key=Note.KEY_A)
        progression = ChordChanges(
            roots=(0, 5, 10, 7), bars_per_chord=2, label="Test", category="Test"
        )

        self.assertEqual(
            [harmony.chord_offset(bar, progression) for bar in range(10)],
            [0, 0, 5, 5, 10, 10, 7, 7, 0, 0],
        )

    def test_chord_root_is_the_progression_step_above_the_key(self) -> None:
        harmony = Harmony(key=Note.KEY_A)

        # A1, then D2 above it, then G1 and E1 below - the nearest octaves
        expected = [55.0, 73.416, 48.999, 41.203]
        for bar, frequency in enumerate(expected):
            self.assertAlmostEqual(
                harmony.chord_freq(55, bar, Progressions.DEEP_HOUSE_MINOR),
                frequency,
                places=2,
            )


class QuantiseTests(unittest.TestCase):
    def test_no_scale_leaves_the_pitch_alone(self) -> None:
        self.assertEqual(Harmony(key=Note.KEY_A).quantise(123.4), 123.4)

    def test_snaps_to_the_nearest_scale_note(self) -> None:
        harmony = Harmony(key=Note.KEY_A, scale=Scales.MINOR)
        # A minor has no C# (138.59 Hz); equidistant from C and C#? no - C#
        # sits a semitone above C and below D, so it snaps down to C
        self.assertAlmostEqual(harmony.quantise(138.59), 130.81, places=1)
        # a note already in the scale is unchanged
        self.assertAlmostEqual(harmony.quantise(220.0), 220.0)
        self.assertAlmostEqual(harmony.quantise(261.63), 261.63, places=1)

    def test_follows_the_key(self) -> None:
        harmony = Harmony(key=0, scale=Scales.MAJOR_PENTATONIC)
        # C major pentatonic: F (349.23) is a semitone from E and 2 from G
        self.assertAlmostEqual(harmony.quantise(349.23), 329.63, places=1)

    def test_result_is_always_in_the_scale(self) -> None:
        harmony = Harmony(key=Note.KEY_A, scale=Scales.MINOR)
        allowed = {(Note.KEY_A + d) % 12 for d in Scales.MINOR.offsets}
        for hz in range(60, 1000, 7):
            snapped = harmony.quantise(float(hz))
            pitch_class = round(69 + 12 * math.log2(snapped / 440)) % 12
            with self.subTest(hz=hz):
                self.assertIn(pitch_class, allowed)


class VoiceTests(unittest.TestCase):
    def test_seventh_chord_is_minor_seventh_in_a_minor_scale(self) -> None:
        self.assertEqual(
            Harmony().voice(Chords.SEVENTH_CHORD, scale=Scales.MINOR),
            (0, 3, 7, 10),
        )

    def test_same_shape_is_major_in_a_major_scale(self) -> None:
        self.assertEqual(Harmony(scale=Scales.MAJOR).voice(Chords.TRIAD), (0, 4, 7))

    def test_negative_degrees_drop_an_octave(self) -> None:
        self.assertEqual(Harmony().voice(Chords.WIDE_POWER_CHORD)[0], -12)

    def test_root_degree_shifts_the_shape_up_the_scale(self) -> None:
        self.assertEqual(
            Harmony(scale=Scales.MAJOR).voice(Chords.TRIAD, root_degree=1),
            (2, 5, 9),
        )


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
