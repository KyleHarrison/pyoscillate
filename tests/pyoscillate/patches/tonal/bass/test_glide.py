"""`glide` and `bend` are live Params on every pitched gated voice that plays a note
line: a profile-driven, FM or funk bass, and the dual-pulse lead. The pitch
signal is checked on stand-in nodes, so no audio server is needed."""

import unittest
from types import SimpleNamespace

from pyoscillate.patches.common import PitchBend
from pyoscillate.patches.tonal.bass.base import AccentBass, Bass
from pyoscillate.patches.tonal.bass.fm.fm import FmBassBark
from pyoscillate.patches.tonal.bass.funk.funk import FunkBass
from pyoscillate.patches.tonal.bass.groove import BassRolling
from pyoscillate.patches.tonal.bass.hover import BassHover
from pyoscillate.patches.tonal.lead.lead import Lead, LeadBrass, LeadMellow70s


class GlideTests(unittest.TestCase):
    def test_every_bass_voice_exposes_it_live_and_sweepable(self) -> None:
        for voice in (BassRolling, BassHover, FmBassBark, FunkBass):
            with self.subTest(voice=voice.__name__):
                self.assertIs(voice.glide.origin, Bass.glide)
                self.assertTrue(voice.glide.sweep)

    def test_defaults_keep_each_voice_sound(self) -> None:
        self.assertEqual(BassRolling.glide.spec.default, 0)
        self.assertEqual(BassHover.glide.spec.default, 0)
        self.assertEqual(FmBassBark.glide.spec.default, 0)
        self.assertEqual(FunkBass.glide.spec.default, 0.02)
        self.assertEqual(LeadBrass.glide.spec.default, 0)
        self.assertEqual(LeadMellow70s.glide.spec.default, 0.02)

    def test_bass_control_sets_the_pitch_glide_time(self) -> None:
        voice = SimpleNamespace(pitch=SimpleNamespace(time=0.0))
        Bass.glide.control(voice, 0.12)
        self.assertEqual(voice.pitch.time, 0.12)

    def test_lead_control_sets_both_oscillators(self) -> None:
        voice = SimpleNamespace(
            pitch1=SimpleNamespace(time=0.0), pitch2=SimpleNamespace(time=0.0)
        )
        Lead.glide.control(voice, 0.08)
        self.assertEqual((voice.pitch1.time, voice.pitch2.time), (0.08, 0.08))

    def test_accent_bass_glide_is_the_shared_one(self) -> None:
        self.assertIs(AccentBass.glide, Bass.glide)

    def test_bend_is_on_every_note_voice_and_defaults_to_clean(self) -> None:
        for voice in (BassRolling, BassHover, FmBassBark, FunkBass, LeadBrass):
            with self.subTest(voice=voice.__name__):
                self.assertIs(voice.bend.origin, PitchBend.bend)
                self.assertEqual(voice.bend.spec.default, 0)
                self.assertTrue(voice.bend.sweep)

    def test_bend_control_sets_the_start_ratio(self) -> None:
        voice = SimpleNamespace(bend_env=SimpleNamespace(mul=0.0))
        PitchBend.bend.control(voice, -12)
        self.assertAlmostEqual(voice.bend_env.mul, -0.5)
        PitchBend.bend.control(voice, 12)
        self.assertAlmostEqual(voice.bend_env.mul, 1.0)
        PitchBend.bend.control(voice, 0)
        self.assertEqual(voice.bend_env.mul, 0.0)


if __name__ == "__main__":
    unittest.main()
