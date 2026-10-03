"""`Lead.detune` is a live, sweepable Param that splits the two pulse oscillators
symmetrically; checked on stand-in nodes, so no audio server is needed."""

import unittest
from types import SimpleNamespace

from pyoscillate.patches.tonal.lead.lead import Lead, LeadBrass, LeadMellow70s


class DetuneTests(unittest.TestCase):
    def test_default_keeps_each_style_sound(self) -> None:
        for voice in (LeadBrass, LeadMellow70s):
            with self.subTest(voice=voice.__name__):
                self.assertIs(voice.detune.origin, Lead.detune)
                self.assertEqual(voice.detune.spec.default, 0)
                self.assertTrue(voice.detune.sweep)

    def test_control_splits_the_oscillators_symmetrically(self) -> None:
        voice = SimpleNamespace(
            detune_up=SimpleNamespace(value=1.0),
            detune_down=SimpleNamespace(value=1.0),
        )
        Lead.detune.control(voice, 0.12)
        self.assertAlmostEqual(voice.detune_up.value, 2 ** (0.12 / 12))
        self.assertAlmostEqual(voice.detune_down.value, 2 ** (-0.12 / 12))
        Lead.detune.control(voice, 0)
        self.assertEqual((voice.detune_up.value, voice.detune_down.value), (1.0, 1.0))


if __name__ == "__main__":
    unittest.main()
