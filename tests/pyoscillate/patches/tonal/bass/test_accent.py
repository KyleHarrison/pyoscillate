"""`AccentBass.accent` couples a step's accent to decay and resonance. The
control's maths is checked on stand-in nodes, so no audio server is needed."""

import unittest
from types import SimpleNamespace

from pyoscillate.patches.tonal.bass.base import AccentBass
from pyoscillate.patches.tonal.bass.groove import BassRolling
from pyoscillate.patches.tonal.bass.hover import BassHover


def _voice(amount: float) -> SimpleNamespace:
    profile = BassRolling.profile
    return SimpleNamespace(
        accent=amount,
        _profile=profile,
        _tempo=SimpleNamespace(sixteenth=0.1),
        envelope=SimpleNamespace(mul=0.0, dur=0.0),
        filtered=SimpleNamespace(res=0.0),
        ACCENT_SHORTEN=AccentBass.ACCENT_SHORTEN,
        ACCENT_SQUELCH=AccentBass.ACCENT_SQUELCH,
        ACCENT_CONTRAST=AccentBass.ACCENT_CONTRAST,
    )


class AccentTests(unittest.TestCase):
    def test_zero_is_level_only(self) -> None:
        voice = _voice(0.0)
        AccentBass.apply_accent(voice, 0.72)

        profile = BassRolling.profile
        self.assertEqual(voice.envelope.mul, 0.72)
        self.assertAlmostEqual(voice.envelope.dur, 0.1 * profile.envelope_decay)
        self.assertEqual(voice.filtered.res, profile.resonance)

    def test_amount_shortens_and_squelches_accented_notes(self) -> None:
        loud, soft = _voice(1.0), _voice(1.0)
        AccentBass.apply_accent(loud, 1.0)
        AccentBass.apply_accent(soft, 0.5)

        self.assertLess(loud.envelope.dur, soft.envelope.dur)
        self.assertGreater(loud.filtered.res, soft.filtered.res)
        self.assertLessEqual(loud.filtered.res, 1.0)

    def test_amount_widens_the_level_contrast(self) -> None:
        flat, wide = _voice(0.0), _voice(1.0)
        AccentBass.apply_accent(flat, 0.5)
        AccentBass.apply_accent(wide, 0.5)

        self.assertLess(wide.envelope.mul, flat.envelope.mul)

    def test_profile_driven_voices_expose_it(self) -> None:
        for voice in (BassRolling, BassHover):
            with self.subTest(voice=voice.__name__):
                self.assertIs(voice.accent.origin, AccentBass.accent)


if __name__ == "__main__":
    unittest.main()
