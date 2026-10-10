"""Perceptual contract for the formant voices (`vocal/singer.py`, `solo.py`,
`ensemble.py`): the notes sung are the rack's chord, Vowel moves the formants,
Throat scales them, Focus sharpens them, Brightness opens the buzz, Breath adds
air, an ensemble's Spread loosens its voices, and the loudest corner stays
clean.

Assertions are directions and tolerance bands, never golden values - see
tests/AGENTS.md. A note is measured once its fade-in and attack are over.

Findings
========

1. Throat made the voice smaller when raised
--------------------------------------------
Error:
    Raising Throat from 0.7 to 1.4 raised the spectral centroid of an open
    'ah' from 594 to 925 Hz, so a "large, deep" throat sounded small and
    bright. The help text promises the opposite.
Cause:
    Throat multiplied the formant frequencies, so a larger value moved every
    formant up, which is what a smaller mouth does.
Change:
    Throat divides the formants: a larger throat lowers them. Checked by the
    same measurement (the centroid now falls from 975 to 630 Hz across the
    range).
Status:
    fixed - src/pyoscillate/patches/tonal/vocal/singer.py.

2. Focus changed the loudness more than the vowel
-------------------------------------------------
Error:
    Focus 0.4 to 3.0 dropped the voice's RMS from 0.037 to 0.010 (-11 dB) on
    an 'ah': a sharper mouth is a lot quieter, so Focus doubled as a level
    control.
Cause:
    A band-pass resonator passes the energy of a broadband buzz in proportion
    to its bandwidth, so every formant lost level as it narrowed.
Change:
    Each formant's level is multiplied by Focus to the power `focus_makeup`
    (0.85, fitted to this measurement: 0.6 left the range 4.5 dB apart), which
    holds the 'ah' within 2 dB of its level across the range.
Status:
    fixed - src/pyoscillate/patches/tonal/vocal/singer.py.
"""

import unittest
from functools import cache

import numpy as np

from pyoscillate.analysis.features import features
from pyoscillate.analysis.render import Render, render
from pyoscillate.analysis.spectrum import Spectrum
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import PATCH_OUTPUT_CEILING, Patch
from pyoscillate.patches.tonal.vocal.ensemble import Angels, Choir
from pyoscillate.patches.tonal.vocal.singer import FormantSinger, VocalTract
from pyoscillate.patches.tonal.vocal.solo import VocalFemale, VocalMale
from pyoscillate.theory.chord import Chords
from pyoscillate.theory.pitch import Note

RATE = 44100
BPM = 120
SOLO = "pyoscillate.patches.tonal.vocal.solo"
ENSEMBLE = "pyoscillate.patches.tonal.vocal.ensemble"
VOICES: tuple[tuple[str, type[FormantSinger]], ...] = (
    (SOLO, VocalFemale),
    (SOLO, VocalMale),
    (ENSEMBLE, Choir),
    (ENSEMBLE, Angels),
)
# the first note's window: after the fade-in and the attack, before the second
# note at 0.5 s (a sparse hook on the eighth grid)
FIRST = (0.3, 0.45)
# settings that take everything but the buzz through the vowel out of the signal
PURE = {"breath": 0, "vibrato": 0, "unsteadiness": 0, "reverb_bal": 0}
# the female voice's first note: the key's root nearest her Register
FIRST_NOTE = Note.A4


def _style(cls: type[Patch]) -> str:
    return cls.name.rsplit("_", 1)[-1]


@cache
def _render(module: str, style: str, seconds: float = 1.2, **params: float) -> Render:
    return render(module, {"style": style, **params}, seconds=seconds, bpm=BPM)


def _female(**params: float) -> Render:
    return _render(SOLO, "female", **{**PURE, **params})


def _first(result: Render) -> Spectrum:
    window = result.samples[round(FIRST[0] * RATE) : round(FIRST[1] * RATE)]
    return Spectrum.of(window, RATE)


class HealthTests(unittest.TestCase):
    def test_render_is_silent_until_the_shared_clock_ticks(self) -> None:
        for module, cls in VOICES:
            with self.subTest(style=cls.name):
                result = features(
                    render(
                        module,
                        {"style": _style(cls)},
                        seconds=0.5,
                        clock_running=False,
                    )
                )

                self.assertLess(result.peak, 1e-4)

    def test_render_sounds_after_the_shared_clock_starts(self) -> None:
        for module, cls in VOICES:
            with self.subTest(style=cls.name):
                result = features(_render(module, _style(cls), seconds=0.8))

                self.assertGreater(result.peak, 1e-3)

    def test_output_stays_under_the_patch_ceiling(self) -> None:
        for module, cls in VOICES:
            with self.subTest(style=cls.name):
                result = _render(module, _style(cls), seconds=2.4)

                self.assertLess(float(abs(result.samples).max()), PATCH_OUTPUT_CEILING)

    def test_the_loudest_corner_stays_under_the_patch_ceiling(self) -> None:
        for module, cls in VOICES:
            own = {param.name for param in cls.params}
            loudest = {
                "brightness": cls.brightness.spec.maximum,
                "breath": cls.breath.spec.maximum,
                "focus": cls.focus.spec.maximum,
                "vowel": 1,
                "reverb_bal": cls.reverb_bal.spec.maximum,
                "reverb_size": cls.reverb_size.spec.maximum,
            }
            with self.subTest(style=cls.name):
                result = _render(
                    module,
                    _style(cls),
                    seconds=2.4,
                    **{name: value for name, value in loudest.items() if name in own},
                )

                self.assertLess(float(abs(result.samples).max()), PATCH_OUTPUT_CEILING)

    def test_a_section_is_about_as_loud_as_a_soloist(self) -> None:
        def level(module: str, cls: type[FormantSinger]) -> float:
            result = _render(module, _style(cls), seconds=2.4)
            window = result.samples[round(0.5 * RATE) : round(2.2 * RATE)]
            return float(20 * np.log10(np.sqrt((window**2).mean())))

        solo = level(SOLO, VocalFemale)

        for module, cls in VOICES[2:]:
            with self.subTest(style=cls.name):
                self.assertLess(abs(level(module, cls) - solo), 6)


class VowelTests(unittest.TestCase):
    def test_a_closed_oo_has_no_energy_where_a_bright_ee_rings(self) -> None:
        closed = _first(_female(vowel=0)).share(1800, 2500)
        bright = _first(_female(vowel=4)).share(1800, 2500)

        self.assertGreater(bright, 4 * closed)

    def test_an_open_ah_puts_its_energy_in_the_first_two_formants(self) -> None:
        # the 'ah' formants (800 and 1150 Hz) sit above the closed vowels'
        # first formant, and below the 'ee''s second
        shares = {
            vowel: _first(_female(vowel=vowel)).share(700, 1400)
            for vowel in (0, 1, 2, 3, 4)
        }

        self.assertEqual(max(shares, key=shares.__getitem__), 2)

    def test_the_vowel_morphs_smoothly_between_neighbours(self) -> None:
        # halfway between two vowels the energy sits between theirs
        low = _first(_female(vowel=3)).share(1800, 2500)
        high = _first(_female(vowel=4)).share(1800, 2500)
        between = _first(_female(vowel=3.5)).share(1800, 2500)

        self.assertGreater(between, min(low, high))
        self.assertLess(between, max(low, high))


class ThroatTests(unittest.TestCase):
    def test_a_larger_throat_lowers_the_formants(self) -> None:
        centroids = [
            _first(_female(throat=throat)).centroid() for throat in (0.7, 1.0, 1.4)
        ]

        self.assertGreater(centroids[0], centroids[1])
        self.assertGreater(centroids[1], centroids[2])


class FocusTests(unittest.TestCase):
    def test_a_sharper_mouth_makes_the_vowel_stand_out_of_its_neighbours(self) -> None:
        # put the open vowel's first formant (800 Hz) on the note's second
        # harmonic: Focus is how much more that harmonic stands over the first
        throat = VocalTract.SOPRANO[2][0][0] / (2 * FIRST_NOTE)

        def contrast(focus: float) -> float:
            levels = _first(_female(throat=throat, focus=focus)).partial_levels(
                FIRST_NOTE, 2
            )
            return float(levels[1] - levels[0])

        soft, sharp = contrast(0.4), contrast(3.0)

        self.assertGreater(sharp, soft + 6)

    def test_focus_keeps_the_open_vowel_at_one_loudness(self) -> None:
        def level(focus: float) -> float:
            samples = _female(focus=focus).samples[
                round(FIRST[0] * RATE) : round(FIRST[1] * RATE)
            ]
            return float(20 * np.log10(np.sqrt((samples**2).mean())))

        levels = [level(focus) for focus in (0.4, 1.0, 3.0)]

        self.assertLess(max(levels) - min(levels), 3)


class ToneTests(unittest.TestCase):
    def test_brightness_opens_the_top_of_the_buzz(self) -> None:
        dark = _first(_female(brightness=500)).share(3000, 20000)
        bright = _first(_female(brightness=9000)).share(3000, 20000)

        self.assertGreater(bright, 10 * dark)

    def test_breath_adds_air_above_the_formants(self) -> None:
        clean = _first(_female(breath=0)).share(6000, 20000)
        breathy = _first(_female(breath=1)).share(6000, 20000)

        self.assertGreater(breathy, 100 * clean)


class ChordTests(unittest.TestCase):
    def test_a_choir_sings_every_tone_of_the_chord(self) -> None:
        patch = Choir()
        patch.harmony = Harmony(key=Note.KEY_A)
        chord = patch.chord_frequencies(0, Chords.SPREAD_TRIAD)
        result = _render(ENSEMBLE, "choir", seconds=2.0, **PURE, spread=0)
        window = result.samples[round(0.8 * RATE) : round(1.8 * RATE)]
        spectrum = Spectrum.of(window, RATE)

        for tone in chord:
            with self.subTest(tone=round(tone, 1)):
                self.assertGreater(
                    spectrum.peak_near(tone, 2), 20 * spectrum.floor_near(tone, 40)
                )

    def test_spread_loosens_the_voices_of_a_note(self) -> None:
        patch = Choir()
        patch.harmony = Harmony(key=Note.KEY_A)
        root = patch.chord_frequencies(0, Chords.SPREAD_TRIAD)[1]

        def tightness(spread: float) -> float:
            result = _render(ENSEMBLE, "choir", seconds=2.0, **PURE, spread=spread)
            window = result.samples[round(0.8 * RATE) : round(1.8 * RATE)]
            spectrum = Spectrum.of(window, RATE)
            return spectrum.band(root - 1.5, root + 1.5) / spectrum.band(
                root - 12, root + 12
            )

        self.assertGreater(tightness(0), 2 * tightness(40))


if __name__ == "__main__":
    unittest.main()
