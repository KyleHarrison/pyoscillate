import unittest

from pyoscillate.theory.intervals import KeysProgression


class KeysProgressionTests(unittest.TestCase):
    def test_every_vamp_has_four_bars_of_four_note_voicings(self) -> None:
        for vamp in KeysProgression:
            with self.subTest(vamp=vamp):
                self.assertEqual(len(vamp.roots), 4)
                for voicing_set in vamp.voicing_sets:
                    self.assertEqual(len(voicing_set), 4)
                    for voicing in voicing_set:
                        self.assertEqual(len(voicing), 4)
                        self.assertEqual(list(voicing), sorted(voicing))

    def test_alternate_set_lifts_only_the_lowest_note(self) -> None:
        for vamp in KeysProgression:
            home, alternate = vamp.voicing_sets
            for home_chord, alt_chord in zip(home, alternate, strict=True):
                with self.subTest(vamp=vamp, chord=home_chord):
                    lifted = sorted((home_chord[0] + 12, *home_chord[1:]))
                    self.assertEqual(list(alt_chord), lifted)

    def test_home_vamp_keeps_the_original_boom_bap_voicings(self) -> None:
        self.assertEqual(KeysProgression.II_V_I_VI.voicing_sets[0][0], (-4, 0, 3, 7))
        self.assertEqual(KeysProgression.II_V_I_VI.roots, (2, 7, 0, 9))
