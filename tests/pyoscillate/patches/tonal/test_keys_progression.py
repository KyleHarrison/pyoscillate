import unittest

from pyoscillate.patches.tonal.keys.keys import Keys
from pyoscillate.theory.harmony import Harmony
from pyoscillate.theory.intervals import Progression, Rhythm, Scale, Voicing

C = 0
D = 2


def _keys(key: int, progression: Progression, inversion: int = 0) -> Keys:
    """A `Keys` with only the state `voicing` reads: no graph, no server."""
    keys = Keys.__new__(Keys)
    keys._harmony = Harmony(key=key, progression=progression)
    keys._inversion = inversion
    return keys


class ProgressionTests(unittest.TestCase):
    def test_every_progression_has_four_roots_inside_an_octave(self) -> None:
        for progression in Progression:
            with self.subTest(progression=progression):
                self.assertEqual(len(progression.roots), 4)
                self.assertTrue(all(0 <= root < 12 for root in progression.roots))

    def test_every_progression_has_a_label_and_round_trips_by_index(self) -> None:
        self.assertEqual(len(Progression.labels()), len(Progression.__members__))
        for index, progression in enumerate(Progression.__members__.values()):
            with self.subTest(progression=progression):
                self.assertIs(Progression.by_index(progression.index), progression)
                self.assertEqual(progression.index, index)

    def test_harmony_reads_roots_from_a_progression_or_a_raw_tuple(self) -> None:
        named = Harmony(progression=Progression.JAZZ_TURNAROUND)
        raw = Harmony(progression=(2, 7, 0, 9))

        self.assertEqual(named.roots, raw.roots)
        self.assertEqual(
            [named.chord_offset(bar) for bar in range(4)],
            [raw.chord_offset(bar) for bar in range(4)],
        )

    def test_every_rhythm_hit_is_on_the_bar_with_a_velocity(self) -> None:
        for rhythm in Rhythm:
            with self.subTest(rhythm=rhythm):
                self.assertTrue(rhythm.hits)
                for step, velocity in rhythm.hits.items():
                    self.assertTrue(0 <= step < rhythm.cycle)
                    self.assertTrue(0 < velocity <= 1)


class ChordTonesTests(unittest.TestCase):
    def test_the_same_shape_is_minor_on_a_ii_and_major_on_a_i(self) -> None:
        harmony = Harmony(key=C, progression=Progression.JAZZ_TURNAROUND)

        # Dm9 without its root: F A C E; Cmaj9 without its root: E G B D
        self.assertEqual(harmony.chord_tones(0, Voicing.ROOTLESS_NINTH), (5, 9, 12, 16))
        self.assertEqual(harmony.chord_tones(2, Voicing.ROOTLESS_NINTH), (4, 7, 11, 14))

    def test_a_root_outside_the_scale_takes_the_nearest_degree(self) -> None:
        self.assertEqual(Scale.MAJOR.degree(1), 0)
        self.assertEqual(Scale.MAJOR.degree(2), 1)


class KeysVoicingTests(unittest.TestCase):
    def test_home_voicings_keep_the_original_boom_bap_chords(self) -> None:
        keys = _keys(C, Progression.JAZZ_TURNAROUND)

        self.assertEqual(keys.voicing(0), (-4, 0, 3, 7))
        # Cmaj9's E G B D, the original voicing's second inversion: the same
        # notes, nearer the centre
        self.assertEqual(keys.voicing(2), (-2, 2, 5, 7))

    def test_every_voicing_is_four_sorted_notes_in_one_close_register(self) -> None:
        for progression in Progression:
            keys = _keys(C, progression)
            for bar in range(4):
                with self.subTest(progression=progression, bar=bar):
                    voicing = keys.voicing(bar)
                    self.assertEqual(len(voicing), 4)
                    self.assertEqual(list(voicing), sorted(voicing))
                    self.assertLess(voicing[-1] - voicing[0], 12)
                    self.assertLess(abs(sum(voicing) / 4 - Keys.voicing_centre), 6)

    def test_a_dominant_chord_gets_a_thirteenth_and_the_rest_a_ninth(self) -> None:
        keys = _keys(C, Progression.JAZZ_TURNAROUND)

        # G13 without its root: B F A E; the other bars are ninths
        # voicings are semitones above Register (A), so add A's pitch class
        self.assertEqual(
            {(note + Keys.register_pitch_class) % 12 for note in keys.voicing(1)},
            {11, 5, 9, 4},
        )
        self.assertEqual(keys.shape(1), Voicing.ROOTLESS_THIRTEENTH)
        for bar in (0, 2, 3):
            self.assertEqual(keys.shape(bar), Voicing.ROOTLESS_NINTH)

    def test_a_minor_v_is_not_taken_for_a_dominant(self) -> None:
        keys = _keys(C, Progression.JAZZ_TURNAROUND)
        keys._harmony.scale = Scale.MINOR

        self.assertEqual(keys.shape(1), Voicing.ROOTLESS_NINTH)

    def test_alternate_inversion_lifts_only_the_lowest_note(self) -> None:
        for bar in range(4):
            home = _keys(C, Progression.JAZZ_TURNAROUND).voicing(bar)
            alternate = _keys(C, Progression.JAZZ_TURNAROUND, inversion=1).voicing(bar)
            with self.subTest(bar=bar):
                self.assertEqual(list(alternate), sorted((home[0] + 12, *home[1:])))

    def test_changing_the_key_transposes_the_chord(self) -> None:
        in_c = _keys(C, Progression.JAZZ_TURNAROUND).voicing(0)
        in_d = _keys(D, Progression.JAZZ_TURNAROUND).voicing(0)

        self.assertEqual(
            sorted(note % 12 for note in in_d),
            sorted((note + D) % 12 for note in in_c),
        )
