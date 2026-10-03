"""The FM harmonic ratio is a live, sweepable Param on both FM voices, and each
style keeps its old ratio as the default; checked on stand-in nodes."""

import unittest
from types import SimpleNamespace

from pyoscillate.patches.tonal.bass.fm.fm import FmBass, FmBassBark, FmBassGrit
from pyoscillate.patches.tonal.lead.fm import LeadFm, LeadFmSwirl, LeadFmWind


class FmRatioTests(unittest.TestCase):
    def test_styles_keep_their_old_ratio(self) -> None:
        cases = (
            (FmBassBark, 1, FmBass),
            (FmBassGrit, 2, FmBass),
            (LeadFmWind, 2.0, LeadFm),
            (LeadFmSwirl, 3.01, LeadFm),
        )
        for voice, default, family in cases:
            with self.subTest(voice=voice.__name__):
                self.assertIs(voice.ratio.origin, family.ratio)
                self.assertEqual(voice.ratio.spec.default, default)
                self.assertTrue(voice.ratio.sweep)

    def test_bass_ratio_stays_on_whole_numbers(self) -> None:
        self.assertEqual(FmBass.ratio.spec.step, 1)

    def test_controls_write_the_operator_ratio(self) -> None:
        bass = SimpleNamespace(tone_signal=SimpleNamespace(ratio=1))
        FmBass.ratio.control(bass, 3)
        self.assertEqual(bass.tone_signal.ratio, 3)
        lead = SimpleNamespace(tone=SimpleNamespace(ratio=2.0))
        LeadFm.ratio.control(lead, 3.01)
        self.assertEqual(lead.tone.ratio, 3.01)


if __name__ == "__main__":
    unittest.main()
